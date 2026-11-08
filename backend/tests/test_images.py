from __future__ import annotations

import re
import shlex
import tomllib
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
REPOSITORY = BACKEND.parent
WORKFLOW = REPOSITORY / ".github" / "workflows" / "ci.yml"

# Both Dockerfiles that install the backend: the compose image, built from
# backend/ alone, and the single-container image the public demo is built
# from.
DOCKERFILES = {
    "backend/Dockerfile": BACKEND / "Dockerfile",
    "Dockerfile": REPOSITORY / "Dockerfile",
}

# pip by any name it can be run under: pip, pip3, pip3.12, python -m pip,
# python3 -m pip, uv pip, a path to one of them, or one of them in exec form.
# uv by any of its commands, though not uv.lock.
PIP = re.compile(r"(?<![\w.-])pip[0-9.]*(?![\w-])")
UV = re.compile(r"(?<![\w.-])uv(?![\w.-])")
# The stage that provides uv. test_versions.py checks its exact form.
UV_IMAGE = re.compile(r"FROM ghcr\.io/astral-sh/uv:\S+ AS uv")

# What an image installs, exported from uv.lock in a stage of its own: the
# runtime dependencies and the image group, which holds pip, and then the
# build group, which holds the project's build requirements. --locked
# refuses a lock that no longer matches pyproject.toml.
EXPORT_IMAGE = (
    "uv export --locked --no-default-groups --group image --no-emit-project"
    " --output-file requirements.txt"
)
EXPORT_BUILD = "uv export --locked --only-group build --output-file build-requirements.txt"
# Every file checked against the hash the lock records and every package from
# a wheel, with nothing resolved: what the list names is all that goes in.
INSTALL_LOCKED = (
    "python -m pip install --no-deps --require-hashes --only-binary=:all: --requirement"
)
# The project's wheel, built with what the build group installed and nothing
# else: no isolated build environment, no index, and a failure if what is
# installed does not meet [build-system].requires.
BUILD_WHEEL = (
    "python -m pip wheel --no-deps --no-build-isolation --check-build-dependencies"
    " --no-index --wheel-dir /wheels ."
)
# The image installs that wheel without anything it would bring with it.
INSTALL_WHEEL = (
    "python -m pip install --no-deps --no-index wheels/electrical_asset_validator-*.whl"
)

# Every line of either Dockerfile that runs pip or uv, with its stage. The
# image itself is the last stage, which has no name.
EXPECTED = [
    ("lock", "COPY --from=uv /uv /usr/local/bin/uv"),
    ("lock", f"RUN {EXPORT_IMAGE} && {EXPORT_BUILD}"),
    ("wheel", f"RUN {INSTALL_LOCKED} build-requirements.txt"),
    ("wheel", f"RUN {BUILD_WHEEL}"),
    ("", f"RUN {INSTALL_LOCKED} requirements.txt"),
    ("", f"RUN {INSTALL_WHEEL} && python -m pip check"),
]

# Options that decide where and how uv export writes its list, rather than
# which packages it lists.
LAYOUT_FLAGS = {"--frozen", "--locked", "--no-annotate", "--no-hashes", "--no-header"}
LAYOUT_OPTIONS = {"--directory", "--output-file"}


def instructions(dockerfile: Path) -> list[tuple[str, str]]:
    """Return every instruction of a Dockerfile with the name of its stage.

    Comment lines are dropped and continuation lines joined, as Docker does,
    and whitespace is collapsed, so an instruction is one line; a line of a
    heredoc counts as one too.
    """
    lines = [
        line
        for line in dockerfile.read_text(encoding="utf-8").splitlines()
        if not line.lstrip().startswith("#")
    ]
    stage = "before the first FROM"
    found: list[tuple[str, str]] = []
    for line in "\n".join(lines).replace("\\\n", " ").splitlines():
        words = line.split()
        if not words:
            continue
        if words[0].upper() == "FROM":
            stage = words[-1] if len(words) > 3 and words[-2].upper() == "AS" else ""
        found.append((stage, " ".join(words)))
    return found


def pip_and_uv(dockerfile: Path) -> list[tuple[str, str]]:
    """Return every instruction that runs pip or uv, with its stage."""
    return [
        (stage, instruction)
        for stage, instruction in instructions(dockerfile)
        if (PIP.search(instruction) or UV.search(instruction))
        and not UV_IMAGE.fullmatch(instruction)
    ]


def selection(command: str) -> list[tuple[str, str]]:
    """Return the options of a uv export that choose what it lists, each with
    its value, if it takes one."""
    words = shlex.split(command)[2:]
    chosen: list[tuple[str, str]] = []
    while words:
        option = words.pop(0)
        value = words.pop(0) if words and not words[0].startswith("-") else ""
        if option not in LAYOUT_FLAGS | LAYOUT_OPTIONS:
            chosen.append((option, value))
    return sorted(chosen)


def workflow_exports() -> dict[str, list[list[tuple[str, str]]]]:
    """Return, for each step of the CI workflow that runs uv export, what each
    of its exports selects."""
    exports: dict[str, list[list[tuple[str, str]]]] = {}
    step = ""
    for line in WORKFLOW.read_text(encoding="utf-8").replace("\\\n", " ").splitlines():
        if line.lstrip().startswith("#"):
            continue
        if match := re.match(r"\s+- name: (.+)$", line):
            step = match.group(1)
        if "uv export" in line:
            exports.setdefault(step, []).append(selection(line[line.index("uv export") :]))
    return exports


@pytest.mark.parametrize("name", DOCKERFILES)
def test_pip_and_uv_run_only_to_install_the_lock(name: str) -> None:
    """No package but the project goes into an image, or into building it,
    unless the lock records it with its hashes."""
    assert pip_and_uv(DOCKERFILES[name]) == EXPECTED


def test_the_lock_holds_the_build_requirements() -> None:
    """The build group is what the images build the project with, so it has
    to be exactly what the project asks its builder for."""
    pyproject = tomllib.loads((BACKEND / "pyproject.toml").read_text(encoding="utf-8"))
    groups = pyproject.get("dependency-groups", {})
    assert groups.get("build") == pyproject["build-system"]["requires"]


def test_ci_audits_and_checks_what_the_images_export() -> None:
    """The audit has to read the two lists the images install from, the image
    check the first of them, and the backend job has to test on both."""
    image = selection(EXPORT_IMAGE)
    build = selection(EXPORT_BUILD)
    assert workflow_exports() == {
        "Check that each image holds exactly the locked set": [image, image],
        "Install backend": [sorted([*image, ("--group", "build"), ("--extra", "dev")])],
        "Audit what the images install": [image, build],
    }
