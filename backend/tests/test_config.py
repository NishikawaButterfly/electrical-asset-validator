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


def test_api_tokens_default_to_disabled_auth() -> None:
    assert Settings().api_tokens == []


def test_api_tokens_parse_from_a_comma_separated_string(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EAV_API_TOKENS", "alpha-team-shared-token, beta-team-shared-token")

    assert Settings().api_tokens == [
        "alpha-team-shared-token",
        "beta-team-shared-token",
    ]


@pytest.mark.parametrize("raw", ["", "   "])
def test_blank_api_tokens_keep_auth_disabled(
    raw: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EAV_API_TOKENS", raw)

    assert Settings().api_tokens == []


@pytest.mark.parametrize("raw", [",", "alpha,,beta", "alpha, ,beta", "alpha,"])
def test_empty_token_entries_are_rejected(
    raw: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EAV_API_TOKENS", raw)

    with pytest.raises(ValueError, match="empty"):
        Settings()


def test_directly_supplied_empty_tokens_are_rejected() -> None:
    with pytest.raises(ValueError, match="empty"):
        Settings(api_tokens=["alpha", ""])
