"""BillBack API. Requests are processed in memory; uploads are never written to disk."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool


from backend.bill_reader import reader as bill_reader
from backend.policy_reader.fetch import MAX_BYTES, FetchError, fetch_policy_pdf
from backend.policy_reader.reader import PolicyReaderError, read_policy

log = logging.getLogger("billback")
app = FastAPI(title="BillBack API")


def _envelope(data: Any = None, error: str | None = None) -> dict[str, Any]:
    return {"success": error is None, "data": data, "error": error}


@app.get("/api/health")
def health() -> dict[str, Any]:
    return _envelope({"ok": True})


async def _pdf_from_request(request: Request) -> tuple[bytes, str | None]:
    ctype = request.headers.get("content-type", "")
    if ctype.startswith("multipart/form-data"):
        form = await request.form()
        upload = form.get("file")
        if upload is None or not hasattr(upload, "read"):
            raise HTTPException(400, "send the PDF as form field 'file'")
        data = await upload.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise HTTPException(413, "file is larger than 25 MB")
        if not data.startswith(b"%PDF"):
            raise HTTPException(400, "file is not a PDF")
        return data, None
    if ctype.startswith("application/json"):
        body = await request.json()
        url = body.get("url") if isinstance(body, dict) else None
        if not isinstance(url, str) or len(url) > 2048:
            raise HTTPException(400, "send {\"url\": \"https://...\"}")
        try:
            return await run_in_threadpool(fetch_policy_pdf, url)
        except FetchError as exc:
            raise HTTPException(400, str(exc)) from exc
    raise HTTPException(415, "send multipart/form-data with 'file', or JSON with 'url'")


@app.post("/api/policy/read")
async def policy_read(request: Request) -> dict[str, Any]:
    pdf_bytes, url = await _pdf_from_request(request)
    try:
        result = await run_in_threadpool(read_policy, pdf_bytes, url=url)
    except PolicyReaderError as exc:
        log.exception("policy reader failed")
        raise HTTPException(502, "could not read that policy; please try again") from exc
    return _envelope(
        {
            "rules": result.rules.model_dump(mode="json"),
            "cached": result.cached,
            "seconds": round(result.seconds, 2),
        }
    )


@app.post("/api/bill/read")
async def bill_read(file: UploadFile) -> dict[str, Any]:
    """Multipart 'file' (photo or PDF). Read into memory only; never saved."""
    data = await file.read(bill_reader.MAX_BILL_BYTES + 1)
    try:
        result = await run_in_threadpool(bill_reader.read_bill, data, file.content_type or "")
    except bill_reader.BillReadError as exc:
        raise HTTPException(400, str(exc)) from exc
    except PolicyReaderError as exc:
        log.exception("bill reader failed")
        raise HTTPException(502, "could not read that bill; please try again") from exc
    return _envelope(result.to_dict())
