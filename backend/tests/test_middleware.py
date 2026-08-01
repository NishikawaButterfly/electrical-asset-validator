from __future__ import annotations

from typing import Any

import pytest

from electrical_asset_validator import middleware as middleware_module
from electrical_asset_validator.middleware import RequestBodyLimitMiddleware

pytestmark = pytest.mark.anyio


async def test_streamed_request_body_is_limited_without_content_length(
    monkeypatch,
) -> None:
    monkeypatch.setattr(middleware_module, "MULTIPART_OVERHEAD_BYTES", 0)
    downstream_completed = False

    async def downstream(scope, receive, send) -> None:
        nonlocal downstream_completed
        while True:
            message = await receive()
            if not message.get("more_body", False):
                break
        downstream_completed = True
        await send({"type": "http.response.start", "status": 204, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    messages: list[dict[str, Any]] = [
        {"type": "http.request", "body": b"123", "more_body": True},
        {"type": "http.request", "body": b"45", "more_body": False},
    ]
    sent: list[dict[str, Any]] = []

    async def receive() -> dict[str, Any]:
        return messages.pop(0)

    async def send(message: dict[str, Any]) -> None:
        sent.append(message)

    application = RequestBodyLimitMiddleware(
        downstream,
        api_prefix="/api/v1",
        max_upload_bytes=4,
    )
    await application(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/validations",
            "headers": [],
        },
        receive,
        send,
    )

    assert downstream_completed is False
    assert sent[0]["type"] == "http.response.start"
    assert sent[0]["status"] == 413
