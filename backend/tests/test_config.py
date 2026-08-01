from __future__ import annotations

import pytest

from electrical_asset_validator.config import Settings


@pytest.mark.parametrize(
    "api_prefix",
    ["", "/", "api/v1", "/api/v1/", "/api//v1"],
)
def test_api_prefix_must_be_an_unambiguous_non_root_path(
    api_prefix: str,
) -> None:
    with pytest.raises(ValueError, match="api_prefix"):
        Settings(api_prefix=api_prefix)


def test_custom_api_prefix_is_preserved() -> None:
    assert Settings(api_prefix="/service/v2").api_prefix == "/service/v2"
