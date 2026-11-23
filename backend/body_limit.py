"""Cap request bodies while they stream in, with or without a Content-Length header (chunked uploads).

Checking Content-Length alone isn't enough: a chunked upload has none, and Starlette would keep reading and spool a
large multipart part to a temp file on disk. This middleware counts body bytes as they arrive and stops at the cap,
so nothing past it is read. The cap is below Starlette's spool threshold (backend/app.py), so uploads stay in memory.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from backend.errors import error_body

Scope = dict[str, Any]
Message = dict[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]


@dataclass
class BodyLimitState:
    max_bytes: int


class _TooLarge(Exception):
    pass


_BODY = json.dumps(error_body("too_large", "file is larger than 25 MB")).encode()
_START = {"type": "http.response.start", "status": 413,
          "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(_BODY)).encode())]}


class BodyLimitMiddleware:
    def __init__(self, app: Callable[..., Awaitable[None]], state: BodyLimitState):
        self.app, self.state = app, state

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        limit = self.state.max_bytes
        length = dict(scope.get("headers") or []).get(b"content-length", b"")
        if length.isdigit() and int(length) > limit:
            await _refuse(send)
            return
        received, over, started = 0, False, False

        async def counted_receive() -> Message:
            nonlocal received, over
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > limit:
                    over = True
                    raise _TooLarge()
            return message

        async def guarded_send(message: Message) -> None:
            nonlocal started
            if over:  # the app turned our abort into its own error (e.g. FastAPI's 400): answer 413 instead
                if message["type"] == "http.response.start" and not started:
                    started = True
                    await send(_START)
                    await send({"type": "http.response.body", "body": _BODY})
                return
            if message["type"] == "http.response.start":
                started = True
            await send(message)

        try:
            await self.app(scope, counted_receive, guarded_send)
        except _TooLarge:
            if not started:
                await _refuse(send)


async def _refuse(send: Send) -> None:
    await send(_START)
    await send({"type": "http.response.body", "body": _BODY})
