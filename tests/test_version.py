"""Tests for stamping the release version into the generated manifests.

The generated manifests carry a placeholder version, and the release workflow
stamps the tag-derived version before it publishes.  That translation is a
contract, so it is pinned here.  ``hatch-vcs`` derives the Python version from
the same tag, and the two agree exactly on a release.
"""

import json
from pathlib import Path

import pytest

from scripts.generate_ts import TS_DIR
from scripts.stamp_version import MANIFESTS, stamp, version_from_tag

# --- Tag to version ---


def test_release_tag_is_used_without_the_leading_v() -> None:
    assert version_from_tag("v0.1.1") == "0.1.1"


def test_release_tag_accepts_multi_digit_components() -> None:
    assert version_from_tag("v12.34.567") == "12.34.567"


@pytest.mark.parametrize(
    "tag",
    [
        "1.2.3",  # no leading v
        "v1.2",  # incomplete version
        "v1.2.3.4",  # too many components
        "v0.1.1-4-gabc1234",  # a commit after the tag, not a release
        "v0.1.1-dirty",  # a dirty tag
        "abc1234",  # a bare commit id
        "",  # nothing at all
    ],
)
def test_a_non_release_tag_raises(tag: str) -> None:
    with pytest.raises(ValueError, match="cannot derive a version"):
        version_from_tag(tag)


# --- Stamping the manifests ---


def test_stamping_writes_the_version_into_every_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Stamping must touch every manifest, or one side would keep 0.0.0."""
    manifests_dir = tmp_path
    for name in MANIFESTS:
        (manifests_dir / name).write_text('{"version": "0.0.0"}\n', encoding="utf-8")
    monkeypatch.setattr("scripts.stamp_version.TS_DIR", manifests_dir)

    stamp("v0.1.1")

    for name in MANIFESTS:
        payload = json.loads((manifests_dir / name).read_text(encoding="utf-8"))
        assert payload["version"] == "0.1.1"


def test_stamping_rejects_a_non_release_tag_before_touching_anything(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A bad tag must not leave a half-stamped tree behind."""
    manifests_dir = tmp_path
    for name in MANIFESTS:
        (manifests_dir / name).write_text('{"version": "0.0.0"}\n', encoding="utf-8")
    monkeypatch.setattr("scripts.stamp_version.TS_DIR", manifests_dir)

    with pytest.raises(ValueError, match="cannot derive a version"):
        stamp("nonsense")

    for name in MANIFESTS:
        payload = json.loads((manifests_dir / name).read_text(encoding="utf-8"))
        assert payload["version"] == "0.0.0"


def test_the_generator_writes_the_placeholder() -> None:
    """The committed manifests must carry the placeholder, not a release."""
    for name in MANIFESTS:
        payload = json.loads((TS_DIR / name).read_text(encoding="utf-8"))
        assert payload["version"] == "0.0.0"
