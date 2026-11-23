#!/usr/bin/env python3
"""Build a sourced Schedule H cross-check file from public ProPublica/IRS data.

No user data is involved. EIN matches are accepted only when the organization name
is an exact/high-confidence match in the same state. Ambiguous facilities are omitted.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import re
import struct
import subprocess
import sys
import urllib.parse
import urllib.request
from urllib.error import HTTPError
import zipfile
import zlib
from dataclasses import dataclass
from datetime import date
from difflib import SequenceMatcher
from html.parser import HTMLParser
from pathlib import Path
from typing import BinaryIO, Iterable
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
POLICY_INDEX = ROOT / "cache" / "policies" / "index.json"
OUTPUT = ROOT / "data" / "schedule_h.json"
PROPUBLICA_SEARCH = "https://projects.propublica.org/nonprofits/api/v2/search.json?q={query}"
PROPUBLICA_SCHEDULE_H = "https://projects.propublica.org/nonprofits/full_text/{object_id}/IRS990ScheduleH"
IRS_INDEX = "https://apps.irs.gov/pub/epostcard/990/xml/{year}/index_{year}.csv"
IRS_ZIP = "https://apps.irs.gov/pub/epostcard/990/xml/{year}/{batch}.zip"
USER_AGENT = "BillBack Schedule H research (https://github.com/MarvinRidgeMT/BillBack)"


def _request(url: str, *, headers: dict[str, str] | None = None, timeout: int = 90):
    merged = {"User-Agent": USER_AGENT, **(headers or {})}
    return urllib.request.urlopen(urllib.request.Request(url, headers=merged), timeout=timeout)


def _json(url: str) -> dict:
    with _request(url) as response:
        return json.load(response)


def _norm(value: str) -> str:
    value = re.sub(r"\([^)]*\)", " ", value.casefold())
    return " ".join(re.findall(r"[a-z0-9]+", value))


def discover_ein(hospital: dict) -> dict | None:
    """Return one conservative ProPublica name/state match, never a best-effort guess."""
    name = hospital["hospital_name"]
    url = PROPUBLICA_SEARCH.format(query=urllib.parse.quote(name))
    try:
        rows = _json(url).get("organizations") or []
    except HTTPError as exc:
        if exc.code == 404:
            return None
        raise
    target = _norm(name)
    candidates = []
    for row in rows:
        candidate = _norm(str(row.get("name") or ""))
        ratio = SequenceMatcher(None, target, candidate).ratio()
        state_match = str(row.get("state") or "").upper() in set(hospital.get("states") or [hospital.get("state")])
        city_match = bool(hospital.get("city")) and str(row.get("city") or "").casefold() == str(hospital["city"]).casefold()
        score = ratio + (0.08 if state_match else 0) + (0.03 if city_match else 0)
        candidates.append((score, ratio, state_match, row))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    score, ratio, state_match, row = candidates[0]
    runner_up = candidates[1][0] if len(candidates) > 1 else 0
    # Exact name in the right state, or an extremely close unique legal-name match.
    if not state_match or ratio < 0.9 or score - runner_up < 0.05:
        return None
    ein = str(row.get("ein") or "").zfill(9)
    if not re.fullmatch(r"\d{9}", ein):
        return None
    return {
        "ein": ein,
        "matched_name": row.get("name"),
        "matched_city": row.get("city"),
        "matched_state": row.get("state"),
        "name_similarity": round(ratio, 3),
        "search_url": url,
    }


def latest_filings(eins: set[str], years: Iterable[int]) -> dict[str, dict]:
    found: dict[str, dict] = {}
    for year in years:
        url = IRS_INDEX.format(year=year)
        with _request(url) as response:
            rows = csv.DictReader(io.TextIOWrapper(response, encoding="utf-8-sig", newline=""))
            for row in rows:
                ein = str(row.get("EIN") or "").zfill(9)
                if ein not in eins or row.get("RETURN_TYPE") != "990" or not row.get("XML_BATCH_ID"):
                    continue
                current = found.get(ein)
                key = (str(row.get("TAX_PERIOD") or ""), str(row.get("SUB_DATE") or ""))
                if current is None or key > current["_key"]:
                    found[ein] = {**row, "_key": key, "index_year": year, "index_url": url}
        if eins.issubset(found):
            break
    return found


class RangeReader(io.RawIOBase):
    """Seekable HTTP reader so zipfile can fetch one XML from a 400+ MB IRS archive."""

    def __init__(self, url: str):
        self.url = url
        with _request(url, headers={"Range": "bytes=0-0"}) as response:
            content_range = response.headers.get("Content-Range", "")
            match = re.search(r"/(\d+)$", content_range)
            if not match:
                raise OSError("IRS archive did not honor byte-range request")
            self.size = int(match.group(1))
        self.position = 0

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.position

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        if whence == io.SEEK_SET:
            position = offset
        elif whence == io.SEEK_CUR:
            position = self.position + offset
        elif whence == io.SEEK_END:
            position = self.size + offset
        else:
            raise ValueError("unsupported seek mode")
        self.position = max(0, min(position, self.size))
        return self.position

    def read(self, size: int = -1) -> bytes:
        if self.position >= self.size:
            return b""
        end = self.size - 1 if size is None or size < 0 else min(self.size - 1, self.position + size - 1)
        start = self.position
        with _request(self.url, headers={"Range": f"bytes={start}-{end}"}) as response:
            data = response.read()
        self.position += len(data)
        return data


def fetch_xml(filing: dict) -> tuple[bytes, str, str]:
    year = int(filing["index_year"])
    batch = filing["XML_BATCH_ID"]
    object_id = filing["OBJECT_ID"]
    zip_url = IRS_ZIP.format(year=year, batch=batch)
    member_suffix = f"{object_id}_public.xml"
    reader = RangeReader(zip_url)
    with zipfile.ZipFile(reader) as archive:
        names = [name for name in archive.namelist() if name.endswith(member_suffix)]
        if len(names) != 1:
            raise LookupError(f"{member_suffix} not found uniquely in {batch}")
        member = names[0]
        info = archive.getinfo(member)
        if info.compress_type not in {9, 20, 93}:
            try:
                return archive.read(member), zip_url, member
            except NotImplementedError as exc:
                raise OSError(f"unsupported IRS ZIP compression method {info.compress_type}") from exc
        # IRS batches use Deflate64 (9) and sometimes Zstandard (20/93), which
        # Python 3.12's zipfile cannot decode. Fetch only this member's range.
        reader.seek(info.header_offset)
        header = reader.read(30)
        if len(header) != 30 or header[:4] != b"PK\x03\x04":
            raise zipfile.BadZipFile("invalid local member header")
        fields = struct.unpack("<4s5H3L2H", header)
        name_length, extra_length = fields[-2], fields[-1]
        reader.seek(info.header_offset + 30 + name_length + extra_length)
        compressed = reader.read(info.compress_size)
        if info.compress_type == 9:
            one_file_zip = _single_member_zip(info, compressed)
            completed = subprocess.run(
                ["bsdtar", "-xOf", "-", info.filename], input=one_file_zip, capture_output=True, check=False
            )
        else:
            completed = subprocess.run(["zstd", "-d", "--stdout", "--quiet"], input=compressed, capture_output=True, check=False)
        if completed.returncode != 0:
            raise OSError("could not decompress IRS Zstandard member")
        data = completed.stdout
        if len(data) != info.file_size or zlib.crc32(data) != info.CRC:
            raise zipfile.BadZipFile("IRS member size or checksum did not match")
        return data, zip_url, member


def _single_member_zip(info: zipfile.ZipInfo, compressed: bytes) -> bytes:
    """Repackage one remotely fetched member so bsdtar can decode Deflate64."""
    clone = zipfile.ZipInfo(info.filename, info.date_time)
    for attribute in (
        "compress_type",
        "CRC",
        "compress_size",
        "file_size",
        "create_system",
        "create_version",
        "extract_version",
        "reserved",
        "internal_attr",
        "external_attr",
    ):
        setattr(clone, attribute, getattr(info, attribute))
    clone.flag_bits = info.flag_bits & ~0x08  # no data descriptor in the rebuilt archive
    clone.extra = b""
    clone.comment = b""
    filename, flag_bits = clone._encodeFilenameFlags()
    local = clone.FileHeader(zip64=False)
    dt = clone.date_time
    dosdate = (dt[0] - 1980) << 9 | dt[1] << 5 | dt[2]
    dostime = dt[3] << 11 | dt[4] << 5 | (dt[5] // 2)
    central = struct.pack(
        zipfile.structCentralDir,
        zipfile.stringCentralDir,
        clone.create_version,
        clone.create_system,
        clone.extract_version,
        clone.reserved,
        flag_bits,
        clone.compress_type,
        dostime,
        dosdate,
        clone.CRC,
        clone.compress_size,
        clone.file_size,
        len(filename),
        0,
        0,
        0,
        clone.internal_attr,
        clone.external_attr,
        0,
    ) + filename
    central_offset = len(local) + len(compressed)
    end = struct.pack(
        zipfile.structEndArchive,
        zipfile.stringEndArchive,
        0,
        0,
        1,
        1,
        len(central),
        central_offset,
        0,
    )
    return local + compressed + central + end


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _truthy(value: str) -> bool:
    return value.strip().casefold() in {"1", "true", "x", "yes"}


def _number(value: str) -> int | None:
    try:
        number = float(value.strip().replace("%", ""))
    except ValueError:
        return None
    if number == 0 or number > 1000:
        return None
    return int(round(number))


def extract_thresholds(xml: bytes) -> dict:
    """Parse Schedule H Part I/Part V FPG fields across schema-year tag variants."""
    root = ET.fromstring(xml)
    free: list[dict] = []
    discounted: list[dict] = []

    def walk(node: ET.Element, parents: tuple[str, ...] = ()) -> None:
        tag = _local(node.tag)
        path = "/".join((*parents, tag))
        compact = re.sub(r"[^a-z0-9]", "", tag.casefold())
        text = (node.text or "").strip()
        destination = free if "freecare" in compact else discounted if ("discount" in compact or "dscnt" in compact) else None
        if destination is not None and ("fpg" in compact or "poverty" in compact):
            value = _number(text)
            if value is None and _truthy(text):
                match = re.search(r"pct(100|150|200|250|300|350|400)", compact)
                value = int(match.group(1)) if match else None
            if value is not None:
                destination.append({"percent": value, "xml_path": path, "verbatim": text})
        for child in node:
            walk(child, (*parents, tag))

    walk(root)

    def unique(values: list[dict]) -> list[dict]:
        seen: set[tuple[int, str]] = set()
        result = []
        for item in values:
            key = (item["percent"], item["xml_path"])
            if key not in seen:
                seen.add(key)
                result.append(item)
        return result

    return {"free_care": unique(free), "discounted_care": unique(discounted)}


class _ScheduleHHTMLParser(HTMLParser):
    """Extract XML-backed fields from ProPublica's IRS Schedule H rendering."""

    def __init__(self) -> None:
        super().__init__()
        self.values: list[dict] = []
        self.active_path: str | None = None
        self.active_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        path = attributes.get("id") or ""
        if tag == "input" and "checked" in attributes:
            label = attributes.get("alt") or path
            match = re.search(r"(100|150|200|250|300|350|400)%", label)
            if match:
                self.values.append({"percent": int(match.group(1)), "xml_path": path, "verbatim": "checked"})
        if tag == "span" and re.search(r"FPGFamilyIncmLmt(?:Free|Dscnt)CarePct", path, re.I):
            self.active_path = path
            self.active_text = []

    def handle_data(self, data: str) -> None:
        if self.active_path is not None:
            self.active_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "span" and self.active_path is not None:
            text = "".join(self.active_text).strip()
            value = _number(text)
            if value is not None:
                self.values.append({"percent": value, "xml_path": self.active_path, "verbatim": text})
            self.active_path = None
            self.active_text = []


def extract_thresholds_from_rendered_html(html: bytes) -> dict:
    """Parse the official XML paths/values shown in ProPublica's Schedule H renderer."""
    parser = _ScheduleHHTMLParser()
    parser.feed(html.decode("utf-8", errors="replace"))
    free = []
    discounted = []
    for item in parser.values:
        marker = f"{item['xml_path']} {item['verbatim']}".casefold()
        if "free" in marker:
            free.append(item)
        elif "discount" in marker or "dscnt" in marker:
            discounted.append(item)

    def unique(items: list[dict]) -> list[dict]:
        by_value_and_path = {(item["percent"], item["xml_path"]): item for item in items}
        return list(by_value_and_path.values())

    return {"free_care": unique(free), "discounted_care": unique(discounted)}


def fetch_rendered_schedule_h(object_id: str) -> tuple[bytes, str]:
    """Fetch ProPublica's rendering, whose element IDs retain IRS XML paths."""
    url = PROPUBLICA_SCHEDULE_H.format(object_id=object_id)
    with _request(url, headers={"Accept-Encoding": "gzip"}) as response:
        data = response.read()
        if response.headers.get("Content-Encoding") == "gzip":
            data = gzip.decompress(data)
    return data, url


def _policy_thresholds(hospital: dict) -> tuple[int | None, int | None]:
    rules = json.loads((POLICY_INDEX.parent / hospital["file"]).read_text())
    free = (rules.get("free_care") or {}).get("fpl_max_percent")
    discounted = (rules.get("discount") or {}).get("fpl_max_percent")
    return (round(free) if isinstance(free, (int, float)) else None, round(discounted) if isinstance(discounted, (int, float)) else None)


def _single(values: list[dict]) -> int | None:
    unique = sorted({item["percent"] for item in values})
    return unique[0] if len(unique) == 1 else None


def build(*, years: list[int]) -> dict:
    hospitals = json.loads(POLICY_INDEX.read_text())["hospitals"]
    matches = {hospital["slug"]: discover_ein(hospital) for hospital in hospitals}
    matches = {slug: match for slug, match in matches.items() if match is not None}
    filings = latest_filings({match["ein"] for match in matches.values()}, years)
    records = []
    for hospital in hospitals:
        match = matches.get(hospital["slug"])
        if not match or match["ein"] not in filings:
            continue
        filing = filings[match["ein"]]
        zip_url = IRS_ZIP.format(year=int(filing["index_year"]), batch=filing["XML_BATCH_ID"])
        xml_path = f"{filing['OBJECT_ID']}_public.xml"
        value_source = "irs_xml"
        rendered_url = None
        try:
            xml, zip_url, xml_path = fetch_xml(filing)
            extracted = extract_thresholds(xml)
        except (OSError, LookupError, zipfile.BadZipFile, ET.ParseError) as exc:
            # Current IRS archives use Deflate64, which Python cannot always
            # decode. ProPublica renders the same e-filed XML and preserves the
            # exact XML path in every value's element ID.
            print(f"rendered fallback {hospital['slug']}: {exc}", file=sys.stderr)
            try:
                html, rendered_url = fetch_rendered_schedule_h(filing["OBJECT_ID"])
                extracted = extract_thresholds_from_rendered_html(html)
                value_source = "propublica_rendered_schedule_h"
            except (HTTPError, OSError) as rendered_exc:
                print(f"skip {hospital['slug']}: {rendered_exc}", file=sys.stderr)
                continue
        filing_free = _single(extracted["free_care"])
        filing_discount = _single(extracted["discounted_care"])
        policy_free, policy_discount = _policy_thresholds(hospital)
        comparisons = [
            (filing_free, policy_free),
            (filing_discount, policy_discount),
        ]
        comparable = [(reported, current) for reported, current in comparisons if reported is not None and current is not None]
        if not comparable:
            continue
        status = "agree" if all(reported == current for reported, current in comparable) else "conflict"
        records.append(
            {
                "hospital_slug": hospital["slug"],
                "hospital_name": hospital["hospital_name"],
                **match,
                "tax_period": filing["TAX_PERIOD"],
                "filing_url": zip_url,
                "xml_path": xml_path,
                "rendered_schedule_h_url": rendered_url,
                "value_source": value_source,
                "object_id": filing["OBJECT_ID"],
                "irs_index_url": filing["index_url"],
                "free_care_fpl_percent": filing_free,
                "discounted_care_fpl_percent": filing_discount,
                "policy_free_care_fpl_percent": policy_free,
                "policy_discounted_care_fpl_percent": policy_discount,
                "status": status,
                "values": extracted,
                "retrieved_date": date.today().isoformat(),
            }
        )
    return {
        "schema_version": 1,
        "generated_date": date.today().isoformat(),
        "sources": {
            "irs_downloads": "https://www.irs.gov/charities-non-profits/form-990-series-downloads",
            "propublica_api": "https://projects.propublica.org/nonprofits/api/",
            "schedule_h_instructions": "https://www.irs.gov/instructions/i990sh",
        },
        "records": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", default="2026,2025,2024", help="IRS index years, newest first")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--stdout", action="store_true")
    args = parser.parse_args()
    result = build(years=[int(year) for year in args.years.split(",")])
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.stdout:
        print(rendered, end="")
    else:
        args.output.write_text(rendered)
        agree = sum(record["status"] == "agree" for record in result["records"])
        conflict = sum(record["status"] == "conflict" for record in result["records"])
        print(f"wrote {len(result['records'])} records: {agree} agree, {conflict} conflict")


if __name__ == "__main__":
    main()
