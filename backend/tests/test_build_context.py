from __future__ import annotations

from pathlib import Path

import pytest

REPOSITORY = Path(__file__).resolve().parents[2]
# The ignore file of the context the root Dockerfile is built from: the
# repository root, where Docker reads no other.
ROOT_IGNORE = REPOSITORY / ".dockerignore"


def patterns(path: Path) -> list[str]:
    """Return the patterns of an ignore file, without comments, blank lines
    or the slashes Docker disregards at either end."""
    return [
        line.strip().strip("/")
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]


@pytest.mark.parametrize("context", ["backend", "frontend"])
def test_the_root_context_leaves_out_what_an_image_context_does(context: str) -> None:
    """compose builds the backend and frontend images from their own
    directories, and the root Dockerfile reads both directories from the
    repository root, so the root file has to leave out what theirs do."""
    root = set(patterns(ROOT_IGNORE))
    missing = [
        pattern
        for pattern in patterns(REPOSITORY / context / ".dockerignore")
        if f"{context}/{pattern}" not in root and f"**/{pattern.removeprefix('**/')}" not in root
    ]
    assert missing == []


def test_the_root_context_leaves_out_what_git_ignores() -> None:
    """A local install, build output, database or .env file is never sent to
    the builder. A gitignore pattern without a slash matches at any depth,
    which in a .dockerignore takes a leading **/."""
    root = set(patterns(ROOT_IGNORE))
    missing = [
        pattern
        for pattern in patterns(REPOSITORY / ".gitignore")
        if not pattern.startswith("!")
        and (f"**/{pattern}" if "/" not in pattern else pattern) not in root
    ]
    assert missing == []
