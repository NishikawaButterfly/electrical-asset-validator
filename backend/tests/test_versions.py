from __future__ import annotations

import json
import re
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPOSITORY = BACKEND.parent
WORKFLOW = REPOSITORY / ".github" / "workflows" / "ci.yml"
DOCKERFILES = (
    REPOSITORY / "Dockerfile",
    BACKEND / "Dockerfile",
    REPOSITORY / "frontend" / "Dockerfile",
)
# CI reads the uv release from this line of backend/Dockerfile with sed, so
# the line has to keep this exact form.
UV_STAGE = re.compile(r"FROM ghcr\.io/astral-sh/uv:([0-9][0-9.]*) AS uv")


def image_tags(image: str) -> list[str]:
    """Return the tag of every FROM line, in any Dockerfile, that names the image."""
    pattern = re.compile(rf"FROM\s+{re.escape(image)}:(\S+)")
    return [
        match.group(1)
        for dockerfile in DOCKERFILES
        for line in dockerfile.read_text(encoding="utf-8").splitlines()
        if (match := pattern.match(line))
    ]


def workflow_values(key: str) -> list[str]:
    """Return every value the CI workflow gives to a setup action input."""
    text = WORKFLOW.read_text(encoding="utf-8")
    return re.findall(rf'^\s+{key}: "?([0-9][0-9.]*)"?$', text, flags=re.MULTILINE)


def release_line(version: str, parts: int) -> str:
    """Return the first parts of a version: 1 gives 22 for 22-alpine."""
    match = re.match(rf"\d+(?:\.\d+){{{parts - 1}}}", version)
    assert match, version
    return match.group()


def test_node_is_one_major_release_everywhere() -> None:
    """setup-node, both Dockerfiles that build the frontend and @types/node
    name one Node major, so a move to a new one has to reach every place."""
    package = json.loads((REPOSITORY / "frontend" / "package.json").read_text(encoding="utf-8"))
    places = {
        "node images": {release_line(tag, 1) for tag in image_tags("node")},
        "setup-node": {release_line(value, 1) for value in workflow_values("node-version")},
        "@types/node": {release_line(package["devDependencies"]["@types/node"], 1)},
    }
    assert len(image_tags("node")) == 2
    assert len({major for majors in places.values() for major in majors}) == 1, places


def test_python_is_one_minor_release_everywhere() -> None:
    """The images and the CI job that tests the backend run the same Python."""
    places = {
        "python images": {release_line(tag, 2) for tag in image_tags("python")},
        "setup-python": {release_line(value, 2) for value in workflow_values("python-version")},
    }
    assert len(image_tags("python")) == 4
    assert len({minor for minors in places.values() for minor in minors}) == 1, places


def test_both_images_export_the_lock_with_the_same_uv() -> None:
    """CI locks and exports with the uv release backend/Dockerfile names, so
    the root Dockerfile has to name the same one."""
    backend_stage = [
        match.group(1)
        for line in (BACKEND / "Dockerfile").read_text(encoding="utf-8").splitlines()
        if (match := UV_STAGE.fullmatch(line))
    ]
    assert len(backend_stage) == 1
    assert image_tags("ghcr.io/astral-sh/uv") == backend_stage * 2
