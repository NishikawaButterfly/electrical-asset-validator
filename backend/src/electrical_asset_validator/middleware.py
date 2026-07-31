from __future__ import annotations

from fastapi import HTTPException
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

MULTIPART_OVERHEAD_BYTES = 1024 * 1024
REQUEST_TOO_LARGE_DETAIL = (
    "The multipart request body is too large for this upload route."
)


class RequestBodyTooLarge(OSError, HTTPException):
    """Trigger multipart-file cleanup while preserving an HTTP 413 response."""

    def __init__(self) -> None:
        OSError.__init__(self, REQUEST_TOO_LARGE_DETAIL)
        HTTPException.__init__(
            self,
            status_code=413,
            detail=REQUEST_TOO_LARGE_DETAIL,
        )


class RequestBodyLimitMiddleware:
    """Reject oversized upload bodies before multipart parsing can spool them."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        api_prefix: str,
        max_upload_bytes: int,
    ) -> None:
        self.app = app
        self.api_prefix = "/" + api_prefix.strip("/")
        self.max_upload_bytes = max_upload_bytes

    def _route_limit(self, scope: Scope) -> int | None:
        if scope.get("type") != "http" or scope.get("method") != "POST":
            return None
        path = str(scope.get("path", "")).rstrip("/")
        if path == f"{self.api_prefix}/validations":
            file_count = 1
        elif path == f"{self.api_prefix}/comparisons":
            file_count = 2
        else:
            return None
        return self.max_upload_bytes * file_count + MULTIPART_OVERHEAD_BYTES

    @staticmethod
    async def _reject(scope: Scope, receive: Receive, send: Send) -> None:
        response = JSONResponse(
            status_code=413,
            content={"detail": REQUEST_TOO_LARGE_DETAIL},
        )
        await response(scope, receive, send)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        limit = self._route_limit(scope)
        if limit is None:
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        content_length = headers.get(b"content-length")
        if content_length is not None:
            try:
                if int(content_length) > limit:
                    await self._reject(scope, receive, send)
                    return
            except ValueError:
                # A malformed value cannot bypass the streaming byte counter.
                pass

        received = 0
        response_started = False

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > limit:
                    raise RequestBodyTooLarge
            return message

        async def tracked_send(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, tracked_send)
        except RequestBodyTooLarge:
            if response_started:
                raise
            await self._reject(scope, receive, send)
