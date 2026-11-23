"""Fetch a policy from a URL (live mode). Public http(s) only, size- and time-capped.

A PDF is returned as bytes. An HTML page is searched for a financial-assistance PDF link; if there is none,
the page's own text is used when it reads like a policy. Every failure has a code the UI explains in EN/ES.
"""

from __future__ import annotations

import html as html_lib
import ipaddress
import re
import socket
import time
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Literal, Optional
from urllib.parse import urljoin, urlparse

import httpx

TIMEOUT_SECONDS = 20.0
MAX_BYTES = 25 * 1024 * 1024
MAX_REDIRECTS = 5
PDF_LINK_WORDS = ("financial", "assistance", "charity", "fap")
POLICY_WORDS = ("financial assistance", "charity care", "poverty", "fpl", "discount", "uninsured")
MIN_HTML_POLICY_CHARS = 1500
USER_AGENT = "BillBack-policy-reader/0.2 (charity-care prototype)"
_HREF_RE = re.compile(r"""href\s*=\s*["']([^"'#]+\.pdf[^"']*)["']""", re.IGNORECASE)


class FetchError(ValueError):
    """The URL could not be fetched as a policy. `code` is stable for the UI; the message is safe to show."""

    def __init__(self, message: str, code: str = "fetch_failed"):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class FetchedPolicy:
    kind: Literal["pdf", "html_text"]
    url: str
    pdf_bytes: bytes = b""
    text: str = ""


ALLOWED_PORTS = (80, 443)
FETCH_DEADLINE_S = 45.0  # wall clock for the whole fetch, so a server dripping bytes can't hold a worker


def _resolve_public(url: str) -> tuple[str, str]:
    """(hostname, one public IP for it). Raises FetchError for non-http(s), odd ports or non-public addresses."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise FetchError("URL must start with http:// or https://", "bad_url")
    try:
        port = parsed.port
    except ValueError as exc:
        raise FetchError("that link has an invalid port", "bad_url") from exc
    if port is not None and port not in ALLOWED_PORTS:
        raise FetchError("that link uses an unusual port", "bad_url")
    try:
        infos = socket.getaddrinfo(parsed.hostname, port or (443 if parsed.scheme == "https" else 80),
                                   proto=socket.IPPROTO_TCP)
    except (socket.gaierror, UnicodeError) as exc:
        raise FetchError("could not find that website", "fetch_failed") from exc
    ips = []
    for info in infos:
        try:
            ip = ipaddress.ip_address(str(info[4][0]).split("%", 1)[0])
        except ValueError as exc:
            raise FetchError("that address is not a public website", "bad_url") from exc
        if not ip.is_global:
            raise FetchError("that address is not a public website", "bad_url")
        ips.append(str(ip))
    if not ips:
        raise FetchError("could not find that website", "fetch_failed")
    return parsed.hostname, ips[0]


def _assert_public_host(url: str) -> None:
    _resolve_public(url)


def _pinned(url: str) -> tuple[str, dict[str, str], dict[str, str]]:
    """Connect to the IP we checked (not a second DNS answer: no DNS rebinding), keeping Host and TLS SNI."""
    host, ip = _resolve_public(url)
    parsed = urlparse(url)
    ip_host = f"[{ip}]" if ":" in ip else ip
    netloc = f"{ip_host}:{parsed.port}" if parsed.port else ip_host
    headers = {"Host": parsed.netloc.rsplit("@", 1)[-1]}
    extensions = {"sni_hostname": host} if parsed.scheme == "https" else {}
    return parsed._replace(netloc=netloc).geturl(), headers, extensions


def _get_capped(client: httpx.Client, url: str, deadline: float | None = None) -> tuple[bytes, str, str]:
    """GET following redirects manually so every hop is checked. Returns (body, content_type, final_url)."""
    deadline = deadline or time.monotonic() + FETCH_DEADLINE_S
    try:
        for _ in range(MAX_REDIRECTS + 1):
            target, headers, extensions = _pinned(url)
            with client.stream("GET", target, headers=headers, extensions=extensions) as resp:
                if resp.is_redirect:
                    url = urljoin(url, resp.headers.get("location", ""))
                    continue
                if resp.status_code != 200:
                    raise FetchError(f"the website returned HTTP {resp.status_code}", "fetch_failed")
                body = bytearray()
                for chunk in resp.iter_bytes():
                    body += chunk
                    if len(body) > MAX_BYTES:
                        raise FetchError("file is larger than 25 MB", "too_large")
                    if time.monotonic() > deadline:
                        raise FetchError("the website took too long to send the file", "fetch_timeout")
                return bytes(body), resp.headers.get("content-type", "").lower(), url
    except httpx.TimeoutException as exc:
        raise FetchError("the website took too long to answer", "fetch_timeout") from exc
    except httpx.HTTPError as exc:
        raise FetchError("could not download from that website", "fetch_failed") from exc
    raise FetchError("too many redirects", "fetch_failed")


def _find_policy_pdf_link(html: str, base_url: str) -> Optional[str]:
    for href in _HREF_RE.findall(html):
        if any(word in href.lower() for word in PDF_LINK_WORDS):
            return urljoin(base_url, html_lib.unescape(href))
    return None


class _TextOnly(HTMLParser):
    SKIP = {"script", "style", "noscript", "nav", "header", "footer", "svg"}

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skipping = 0

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in self.SKIP:
            self._skipping += 1
        elif tag in ("p", "br", "li", "h1", "h2", "h3", "h4", "tr", "div"):
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self.SKIP and self._skipping:
            self._skipping -= 1

    def handle_data(self, data: str) -> None:
        if not self._skipping:
            self.parts.append(data)


def html_to_text(html: str) -> str:
    parser = _TextOnly()
    parser.feed(html)
    text = "".join(parser.parts)
    lines = [re.sub(r"[ \t\xa0]+", " ", ln).strip() for ln in text.splitlines()]
    return "\n".join(ln for ln in lines if ln)


def looks_like_policy(text: str) -> bool:
    low = text.lower()
    return sum(word in low for word in POLICY_WORDS) >= 2


def fetch_policy(url: str) -> FetchedPolicy:
    if not isinstance(url, str) or not url.strip():
        raise FetchError("paste a link that starts with https://", "bad_url")
    with httpx.Client(timeout=TIMEOUT_SECONDS, follow_redirects=False, headers={"User-Agent": USER_AGENT}) as client:
        deadline = time.monotonic() + FETCH_DEADLINE_S
        body, ctype, final_url = _get_capped(client, url.strip(), deadline)
        if body.startswith(b"%PDF") or "application/pdf" in ctype:
            if not body.startswith(b"%PDF"):
                raise FetchError("the file says it is a PDF but isn't one", "not_pdf")
            return FetchedPolicy("pdf", final_url, pdf_bytes=body)
        if "text/html" not in ctype:
            raise FetchError("that link is not a PDF or a web page", "not_pdf")
        page = body.decode("utf-8", errors="ignore")
        link = _find_policy_pdf_link(page, final_url)
        if link:
            body, _, final_url = _get_capped(client, link, deadline)
            if not body.startswith(b"%PDF"):
                raise FetchError("the policy link on that page is not a PDF", "not_pdf")
            return FetchedPolicy("pdf", final_url, pdf_bytes=body)
        text = html_to_text(page)
        if len(text) >= MIN_HTML_POLICY_CHARS and looks_like_policy(text):
            return FetchedPolicy("html_text", final_url, text=text)
        raise FetchError("no financial assistance policy found on that page", "no_pdf_link")


def fetch_policy_pdf(url: str) -> tuple[bytes, str]:
    """Back-compat: PDF bytes only (raises FetchError for an HTML-only policy)."""
    got = fetch_policy(url)
    if got.kind != "pdf":
        raise FetchError("that page has the policy as text, not a PDF", "no_pdf_link")
    return got.pdf_bytes, got.url
