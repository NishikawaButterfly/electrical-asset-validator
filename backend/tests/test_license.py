from __future__ import annotations

from pathlib import Path

# license-files paths may not leave the directory that holds pyproject.toml,
# and the compose image is built from backend/ alone, so the distributions
# ship this copy rather than the LICENSE at the repository root.
BACKEND_LICENSE = Path(__file__).resolve().parents[1] / "LICENSE"
REPOSITORY_LICENSE = Path(__file__).resolve().parents[2] / "LICENSE"


def test_backend_license_matches_the_repository_license() -> None:
    """The license the distributions ship must be the one the repository states."""
    assert BACKEND_LICENSE.read_bytes() == REPOSITORY_LICENSE.read_bytes()
