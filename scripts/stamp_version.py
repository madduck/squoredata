#!/usr/bin/env python3
"""Stamp the release version into the generated TypeScript manifests.

The generated manifests carry the placeholder ``0.0.0``, because they are
version-independent artefacts: they describe the models, not a release.  The
version is release metadata, so the release workflow runs this script to
rewrite the ``version`` field in ``typescript/package.json`` and
``typescript/jsr.json`` from the Git tag before it publishes.

Usage::

    python scripts/stamp_version.py v0.1.1

The tag is the single source of truth, the same one ``hatch-vcs`` uses to
version the Python wheel.
"""

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TS_DIR = REPO_ROOT / "typescript"

# ``v1.2.3``: the release tag.  The leading ``v`` is not part of the version.
_TAG_RE = re.compile(r"^v(?P<version>\d+\.\d+\.\d+)$")

# The manifests carry the placeholder, and the release overwrites it.
MANIFESTS = ("package.json", "jsr.json")


def version_from_tag(tag: str) -> str:
    """Translate a release tag into an npm version.

    ``v0.1.1`` becomes ``0.1.1``.  The result is deliberately *not* the PEP 440
    version hatch-vcs produces for the wheel; the two identify the same release
    for different registries.

    Args:
        tag: A Git tag, as the release workflow reports it.

    Returns:
        The version without its leading ``v``.

    Raises:
        ValueError: If ``tag`` is not a ``v<major>.<minor>.<patch>`` tag,
            because then the version cannot be trusted.
    """
    if match := _TAG_RE.match(tag):
        return match["version"]
    raise ValueError(f"cannot derive a version from {tag!r}")


def stamp(tag: str) -> None:
    """Write the version derived from ``tag`` into every manifest.

    Args:
        tag: The Git tag to derive the version from.

    Raises:
        ValueError: If ``tag`` is not a release tag.
    """
    version = version_from_tag(tag)
    for name in MANIFESTS:
        path = TS_DIR / name
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["version"] = version
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: stamp_version.py <tag>")
    stamp(sys.argv[1])
