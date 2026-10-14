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
- `scripts/generate_ts.py` — renders JSON Schema from the models, converts it
  to TypeScript, and writes the runtime validators and package metadata.
- `scripts/make_golden.py` — regenerates `golden/*.json`.
- `typescript/` — the published npm package: generated `.d.ts` files, the Ajv
  validators (`index.js`), `schemas/`, `package.json`, and `LICENSE`.
- `hatch_build.py` — Hatchling hook that runs the generator.

## Publishing

The Python package and the npm package share one version, taken from
`pyproject.toml`. To release the npm package by hand:

```sh
python scripts/generate_ts.py
git diff --exit-code typescript/   # must be clean before publishing
npm --prefix typescript publish --access public
```

`--access public` is not optional: scoped packages default to private, and a
private publish requires a paid npm plan. Publishing a version is irreversible,
so run the full definition of done first.

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

The npm package is `@madduck/squoredata`, published from `typescript/`. The
JSON Schema is the single source of truth: the interfaces and the runtime
validators are both derived from it.

- `scripts/generate_ts.py` uses `model_json_schema(mode="serialization")`, which
  is the wire format and therefore includes the computed fields.
- The generator writes `<Model>.schema.json` and `<Model>.d.ts` for json2ts's
  own use, plus the shippable artefacts: `schemas/<Model>.schema.json`,
  `index.js`, `index.d.ts`, `package.json`, and a copy of `LICENSE`.
- Because Pydantic emits no `$schema` key, the generator stamps
  `https://json-schema.org/draft/2020-12/schema` into every schema. Without it
  Ajv would fall back to draft-07 while the models follow draft 2020-12.
- The generated `package.json` is built from a template inside
  `generate_ts.py`; its `version` is read from `pyproject.toml`, so the npm and
  Python versions always mirror each other. The version is **not** set by hand.
- `index.js` compiles the schemas with Ajv
  (`ajv/dist/2020.js`) and exports `validateSquoreMatch`,
  `validateSquoreMatchLiveData`, and `schemas`.
- `index.d.ts` re-exports only the public interfaces with explicit
  `export type { X } from "./X"`. A plain `export *` collides, because
  `json-schema-to-typescript` emits dozens of helper type aliases (`A`, `B1`, …)
  into each file and the two model files share names.
- `Game.score` and the computed `scores` use a plain serializer that converts
  tuples to lists. Without it, json2ts loses the element typing and emits
  `[unknown, unknown]`.
- Regenerate with `python scripts/generate_ts.py` after any model change, and
  commit the output.

### Validation scope

The runtime validators pass `validateFormats: false`. The Python models accept
timestamps without a UTC offset, but Ajv's strict `date-time` pattern rejects
them, so enabling format checks would reject valid data on one side while
Python accepts it. The validators therefore check structure only: types,
required properties, and forbidden extra properties. Do not turn format
checking on without first proving the golden files still validate.

## Golden tests

`golden/*.json` are serialized model instances and are the shared contract
between Python and TypeScript:

- `tests/test_golden.py` validates the golden files against the models and
  round-trips them. Because computed fields are not valid input, the test strips
  them (`games`, `scores`, `status`, `winner`) before validating.
- `typescript/tests/golden.ts` assigns the same files to the generated
  interfaces, so `tsc --noEmit` fails when the two sides diverge.
- `typescript/tests/golden.test.js` runs the generated validators against the
  same files, and asserts that they reject an extra property, a missing required
  property, and a wrong type. A validator test that cannot fail is worthless, so
  keep those negative cases.

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

Bandit configuration lives in the `[tool.bandit]` section of
`pyproject.toml`, so all tool configuration stays in one file. Bandit does
**not** read that section on its own: it must be pointed at the file
explicitly.

```sh
bandit -c pyproject.toml -r .
```

Forgetting `-c pyproject.toml` fails silently. Bandit then uses its built-in
defaults, descends into `.venv`, and reports thousands of findings from
third-party code without any error. Always pass the flag.

The `exclude_dirs` list keeps the scan out of `.venv`, `.direnv`, `.git`, and
`node_modules`. The nested `[tool.bandit.assert_used]` section skips `B101`
(`assert`) for the test files, which would otherwise dominate the report.

Exclusion patterns should carry a wildcard, such as `**/.venv/*`. A bare
directory name works in the `-c` path, but Bandit rewrites a bare existing
directory name into `<name>/*` in its INI configuration path, and that glob
then matches nothing, so the wildcard form is the one that keeps working if
the configuration ever moves back into a `.bandit` file.

There must be exactly **one** Bandit configuration. Bandit auto-discovers a
project-level `.bandit` file while walking the target, so leaving one behind
alongside the `pyproject.toml` section gives two sources of truth and
unpredictable results.

## Definition of done

Run the same checks CI runs, on Python 3.13 and 3.14 where practical:

```sh
ruff check .
pytest
mypy --strict .
bandit -c pyproject.toml -r .
npm install
python scripts/generate_ts.py
git diff --exit-code typescript/
npm test
```

`npm test` runs both the type check (`tsc --noEmit`) and the runtime golden
tests (`node --test`).

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
- Do not add a second Bandit configuration file; `pyproject.toml` is the only
  one, and Bandit must be invoked with `-c pyproject.toml`.
- Do not commit generated TypeScript without regenerating it from the models.
- Do not let a build reach the network; the hook guards against this.
- Do not weaken the strict mypy settings or `extra="forbid"` to make something
  pass.
