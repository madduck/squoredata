# squoredata

Guidance for coding agents working in this repository. Read this together with
the user-level `AGENTS.md`, which takes precedence where the two overlap.

## What this project is

`squoredata` is a small, self-contained library of the Pydantic v2 data
structures that a [Squore](https://github.com/obbimi/Squore) scoreboard tablet
uses. It was extracted from the `tcboard` server so that both the Python server
and JavaScript/TypeScript clients can share one definition of the data.

It contains only data models and their derived accessors, no server logic, no
I/O, and no network code. The only runtime dependency is `pydantic`.

The model set:

- `SquoreMatch` — a match without live information (players, event, format,
  metadata, …).
- `SquoreMatchLiveData` — a `SquoreMatch` plus the live data a tablet reports.
  It adds the `court` and `timestamp` fields.
- Supporting models: `Players`, `PlayersProps`, `Colors`, `Countries`, `Clubs`,
  `Event`, `Format`, `Wifi`, `Metadata`, `SquoreDeviceInfo`, `BatteryStatus`,
  `DeviceInfo`, `TimerInfo`, `Timing`, `When`, `Point`, `Game`.
- Types and enums: `PlayerLetter`, `PlayerIndex`, `ServerSide`, `AppealType`,
  `ServerType`, `LockStateType`, `ScoreType`, `ScoresType`, `Result`,
  `LiveStatus`.
- `InconsistentStateError`, raised by `validate_livedata`.

`SquoreMatchLiveData.status`, `.scores`, `.games` and `.winner` are computed
fields and therefore part of the serialized (wire) format.

## Layout

- `src/squoredata/` — the package, one module per concern: `match.py`,
  `livedata.py`, `devinfo.py`, `game.py`, `point.py`, `livestatus.py`.
- `tests/` — mirrors the modules; fixtures in `tests/conftest.py`.
- `golden/` — the shared golden fixtures (see below).
- `golden_data.py` — builders for the golden instances, at the repo root so both
  the tests and the generation script import one source of truth.
- `scripts/generate_ts.py` — renders JSON Schema from the models and converts it
  to TypeScript.
- `scripts/make_golden.py` — regenerates `golden/*.json`.
- `typescript/` — generated `.d.ts` files, JSON Schemas, `index.d.ts`, and the
  `package.json` that consumers install from.
- `hatch_build.py` — Hatchling hook that runs the generator.

## Conventions

- Python 3.13+; 4-space indent; Google-style docstrings on public functions;
  type hints everywhere, including tests; `pathlib`, f-strings.
- Typing is strict: `mypy --strict` plus `warn_unreachable`. Do not add
  `# type: ignore` without a reason.
- Ruff with `line-length = 88`, lint select
  `["B", "C", "E", "F", "I", "W", "B9"]`.
- Models are Pydantic v2 `BaseModel`s. The Squore input models use
  `extra="forbid"` so unexpected tablet fields fail loudly.
- `from __future__ import annotations` appears in modules that need it for
  Python < 3.14; keep it where present.

## Tests

- `pytest` is configured for coverage (`--cov=squoredata`), `--ruff`, and
  `--ruff-format`.
- Everything is expected to be test-covered, and typing counts as part of
  coverage. New behaviour needs new tests.
- Prefer the existing fixtures in `tests/conftest.py` over building fixtures
  inline.
- Test names are descriptive sentences; sections are separated by
  `# --- Name ---` comment rules.

## TypeScript generation

- `scripts/generate_ts.py` uses `model_json_schema(mode="serialization")`, which
  is the wire format and therefore includes the computed fields.
- The generator writes both `<Model>.schema.json` and `<Model>.d.ts`, plus
  `index.d.ts`.
- `index.d.ts` re-exports only the public interfaces with explicit
  `export type { X } from "./X"`. A plain `export *` collides, because
  `json-schema-to-typescript` emits dozens of helper type aliases (`A`, `B1`, …)
  into each file and the two model files share names.
- `Game.score` and the computed `scores` use a plain serializer that converts
  tuples to lists. Without it, json2ts loses the element typing and emits
  `[unknown, unknown]`.
- Regenerate with `python scripts/generate_ts.py` after any model change, and
  commit the output.

## Golden tests

`golden/*.json` are serialized model instances and are the shared contract
between Python and TypeScript:

- `tests/test_golden.py` validates the golden files against the models and
  round-trips them. Because computed fields are not valid input, the test strips
  them (`games`, `scores`, `status`, `winner`) before validating.
- `typescript/tests/golden.ts` assigns the same files to the generated
  interfaces, so `tsc --noEmit` fails when the two sides diverge.

Regenerate the golden files with `python scripts/make_golden.py` after a model
change. A golden test that cannot fail is worthless: when you change a golden
file or a model, confirm that both sides actually reject a deliberate mismatch.

## Build and packaging

- `pip install -e .[dev]` for development; `python -m build` for a release.
- `[build-system].requires` includes `pydantic`, because the build hook imports
  the models to render their schemas.
- `hatch_build.py` runs the generator **only** when `node_modules/.bin/json2ts`
  exists. A build must never reach the network, so an isolated build without
  Node tooling ships the committed bindings as they are. Drift in the committed
  bindings is caught by CI, which installs the Node dependencies, regenerates,
  and fails on `git diff`.
- The sdist deliberately includes `scripts/`, `typescript/`, `golden/`,
  `golden_data.py`, and `hatch_build.py` so it is self-contained.

## Packaging pitfalls (learned the hard way)

- `py.typed` is not optional. A consumer that runs `mypy --strict` against a
  package that lacks it gets `import-untyped` and silent `Any` propagation,
  which then makes the consumer's own `# type: ignore` comments look unused.
- `pip install <local path>` runs the build hook during metadata generation. If
  the hook writes into the source tree, the install fails on a read-only
  checkout. Installing a local path is therefore not a substitute for publishing
  a wheel.
- Pre-commit's mypy hook runs in an isolated environment that only sees
  `additional_dependencies` from PyPI. A local-path dependency is installed by
  re-running the build, so any build-hook failure surfaces there too.

## Bandit

Bandit reads its configuration from the project-level `.bandit` file. Bandit
1.9.4 does not read `pyproject.toml`, so a `[tool.bandit]` section has no
effect.

The `exclude` list in `.bandit` keeps the scan out of `.venv`, `.direnv`,
`.git`, and `node_modules`. Without it, a recursive scan descends into the
virtualenv and reports thousands of findings from third-party code.

Each exclusion pattern must contain a wildcard. Bandit rewrites a bare existing
directory name (`exclude = .venv`) into `.venv/*`, and that glob then matches
nothing, so the exclusion silently stops working. Use `**/.venv/*` and similar
patterns.

## Definition of done

Run the same checks CI runs, on Python 3.13 and 3.14 where practical:

```sh
ruff check .
pytest
mypy --strict .
bandit -r .
npm install
python scripts/generate_ts.py
git diff --exit-code typescript/
node_modules/.bin/tsc --noEmit -p tsconfig.json
```

## Commits

Follow the user-level Git rules. In addition:

- Short, imperative subject lines without a trailing period or a type/scope
  prefix, 80 characters max.
- Bundle tests, code, generated bindings, and documentation for one behaviour
  into a single commit.
- If a model changes, the regenerated `typescript/` and `golden/` files belong
  in the same commit as the model.

## Things to avoid

- Do not remove `py.typed`.
- Do not remove the wildcards from the `exclude` patterns in `.bandit`.
- Do not commit generated TypeScript without regenerating it from the models.
- Do not let a build reach the network; the hook guards against this.
- Do not weaken the strict mypy settings or `extra="forbid"` to make something
  pass.
