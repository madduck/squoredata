#!/usr/bin/env python3
"""Regenerate the committed golden JSON files.

The golden files are the shared contract between the Python and the TypeScript
side.  Regenerate them with::

    python scripts/make_golden.py

After regenerating, run ``python scripts/generate_ts.py`` (also done by the
build hook) and the test suites on both sides.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GOLDEN_DIR = REPO_ROOT / "golden"

sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from golden_data import GOLDEN  # noqa: E402


def main() -> None:
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    for filename, factory in GOLDEN.items():
        model = factory()  # type: ignore[operator]
        payload = model.model_dump(mode="json")
        path = GOLDEN_DIR / filename
        path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(f"wrote {path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
