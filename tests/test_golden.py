"""Golden tests: validate the shared contract on the Python side.

The files in ``golden/`` are the single source of truth shared with the
TypeScript side.  ``typescript/tests/golden.ts`` assigns the very same files to
the generated interfaces, so ``tsc`` fails whenever the two sides diverge.
"""

import json
from pathlib import Path
from typing import Any

import pytest

from squoredata import SquoreMatch, SquoreMatchLiveData

GOLDEN_DIR = Path(__file__).resolve().parent.parent / "golden"

COMPUTED_FIELDS = frozenset({"games", "scores", "status", "winner"})


def _load(filename: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(
        (GOLDEN_DIR / filename).read_text(encoding="utf-8")
    )
    return data


def _without_computed(payload: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in payload.items() if k not in COMPUTED_FIELDS}


def test_squore_match_serialises_to_golden() -> None:
    from golden_data import squash_golden_match

    assert squash_golden_match().model_dump(mode="json") == _load("squore-match.json")


def test_squore_match_validates_golden() -> None:
    payload = _load("squore-match.json")
    match = SquoreMatch.model_validate(_without_computed(payload))
    assert match.model_dump(mode="json") == payload


def test_squore_match_livedata_serialises_to_golden() -> None:
    from golden_data import golden_match_livedata

    assert golden_match_livedata().model_dump(mode="json") == _load(
        "squore-match-livedata.json"
    )


def test_squore_match_livedata_validates_golden() -> None:
    payload = _load("squore-match-livedata.json")
    match = SquoreMatchLiveData.model_validate(_without_computed(payload))
    assert match.model_dump(mode="json") == payload


@pytest.mark.parametrize(
    "filename, expected",
    [
        ("squore-match-livedata.json", {"status": 3, "winner": None}),
    ],
)
def test_golden_computed_fields(filename: str, expected: dict[str, Any]) -> None:
    payload = _load(filename)
    for key, value in expected.items():
        assert payload[key] == value


def test_typescript_golden_files_are_generated() -> None:
    """The TypeScript side must consume exactly the committed golden files."""
    ts_test = (
        Path(__file__).resolve().parent.parent / "typescript" / "tests" / "golden.ts"
    )
    assert ts_test.exists()
    for name in ("squore-match.json", "squore-match-livedata.json"):
        assert f"golden/{name}" in ts_test.read_text(encoding="utf-8")
