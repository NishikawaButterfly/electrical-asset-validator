from __future__ import annotations

import shlex
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
REPOSITORY = BACKEND.parent

# Both Dockerfiles that install the backend: the compose image, built from
# backend/ alone, and the single-container image the public demo is built
# from.
DOCKERFILES = {
    "backend/Dockerfile": BACKEND / "Dockerfile",
    "Dockerfile": REPOSITORY / "Dockerfile",
}

# The packages an image installs are the runtime dependencies and the image
# group (the pip release the image upgrades to), exported from uv.lock.
# --locked refuses a lock that no longer matches pyproject.toml.
EXPORT = [
    "uv",
    "export",
    "--locked",
    "--no-default-groups",
    "--group",
    "image",
    "--no-emit-project",
    "--output-file",
    "requirements.txt",
]
# Every file checked against the hash the lock records, every package from a
# wheel, and nothing resolved: what the export lists is all that goes in.
INSTALL_LOCK = [
    "--no-deps",
    "--require-hashes",
    "--only-binary=:all:",
    "--requirement",
    "requirements.txt",
]
# Then the project itself, which must not bring anything with it.
INSTALL_PROJECT = ["--no-deps", "."]


def run_commands(dockerfile: Path) -> list[list[str]]:
    """Split every RUN instruction of a Dockerfile into its shell commands."""
    text = dockerfile.read_text(encoding="utf-8").replace("\\\n", " ")
    commands: list[list[str]] = []
    for line in text.splitlines():
        instruction, _, arguments = line.strip().partition(" ")
        if instruction.upper() == "RUN":
            commands.extend(shlex.split(command) for command in arguments.split("&&"))
    return commands


@pytest.mark.parametrize("name", DOCKERFILES)
def test_image_exports_its_packages_from_the_lock(name: str) -> None:
    exports = [command for command in run_commands(DOCKERFILES[name]) if command[:2] == EXPORT[:2]]
    assert exports == [EXPORT]


@pytest.mark.parametrize("name", DOCKERFILES)
def test_image_installs_the_lock_and_then_only_the_project(name: str) -> None:
    """No pip install may run but these two, so no version enters an image
    that the lock does not record."""
    installs = [
        command[4:]
        for command in run_commands(DOCKERFILES[name])
        if command[:4] == ["python", "-m", "pip", "install"]
    ]
    assert installs == [INSTALL_LOCK, INSTALL_PROJECT]
