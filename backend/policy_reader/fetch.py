"""Fetch a policy PDF from a URL (live mode). Public http(s) only, size- and time-capped."""

from __future__ import annotations

import ipaddress
import re
import socket
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx

TIMEOUT_SECONDS = 20.0
MAX_BYTES = 25 * 1024 * 1024
MAX_REDIRECTS = 5
PDF_LINK_WORDS = ("financial", "assistance", "charity", "fap")
USER_AGENT = "BillBack-policy-reader/0.1 (hackathon prototype)"
_HREF_RE = re.compile(r"""href\s*=\s*["']([^"'#]+\.pdf[^"']*)["']""", re.IGNORECASE)


class FetchError(ValueError):
    """The URL could not be fetched as a policy PDF. Message is safe to show users."""


def _assert_public_host(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise FetchError("URL must start with http:// or https://")
    try:
        infos = socket.getaddrinfo(parsed.hostname, parsed.port or 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise FetchError("could not resolve that website") from exc
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if not ip.is_global:
            raise FetchError("that address is not a public website")


def _get_capped(client: httpx.Client, url: str) -> tuple[bytes, str, str]:
    """GET following redirects manually so every hop is checked. Returns (body, content_type, final_url)."""
    for _ in range(MAX_REDIRECTS + 1):
        _assert_public_host(url)
        with client.stream("GET", url) as resp:
            if resp.is_redirect:
                url = urljoin(url, resp.headers.get("location", ""))
                continue
            if resp.status_code != 200:
                raise FetchError(f"website returned HTTP {resp.status_code}")
            body = bytearray()
            for chunk in resp.iter_bytes():
                body += chunk
                if len(body) > MAX_BYTES:
                    raise FetchError("file is larger than 25 MB")
            return bytes(body), resp.headers.get("content-type", "").lower(), str(resp.url)
    raise FetchError("too many redirects")


def _find_policy_pdf_link(html: str, base_url: str) -> Optional[str]:
    for href in _HREF_RE.findall(html):
        if any(word in href.lower() for word in PDF_LINK_WORDS):
            return urljoin(base_url, href)
    return None


def fetch_policy_pdf(url: str) -> tuple[bytes, str]:
    """Return (pdf_bytes, final_pdf_url). An HTML page is searched for a FAP-looking PDF link."""
    with httpx.Client(timeout=TIMEOUT_SECONDS, follow_redirects=False, headers={"User-Agent": USER_AGENT}) as client:
        body, ctype, final_url = _get_capped(client, url)
        if body.startswith(b"%PDF") or "application/pdf" in ctype:
            return body, final_url
        if "text/html" not in ctype:
            raise FetchError("URL is not a PDF or a web page")
        link = _find_policy_pdf_link(body.decode("utf-8", errors="ignore"), final_url)
        if not link:
            raise FetchError("no financial assistance PDF link found on that page")
        body, ctype, final_url = _get_capped(client, link)
        if not body.startswith(b"%PDF"):
            raise FetchError("linked file is not a PDF")
        return body, final_url
