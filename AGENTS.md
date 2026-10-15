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
- `scripts/stamp_version.py` — writes the tag-derived version into the generated
  TypeScript manifests; the release workflow runs it before packing or
  publishing.
- `scripts/__init__.py` — package marker, so `scripts.generate_ts` has one
  module name for mypy.
- `typescript/` — the published npm package: generated `.d.ts` files, the Ajv
  validators (`index.js`), `schemas/`, `package.json`, and `LICENSE`.
- `hatch_build.py` — Hatchling hook that runs the generator.

## Publishing

The Python package and the JSR package share one version, derived from the Git
tag. `pyproject.toml` declares the version dynamic and `hatch-vcs` resolves it,
so there is no version literal to forget. `raw-options = { local_scheme =
"no-local-version" }` drops the PEP 440 local segment, which npm and JSR would
reject. The generated TypeScript manifests are version-independent: they
always carry the placeholder `0.0.0`, and the release workflow stamps the
tag-derived version into them with `scripts/stamp_version.py` before it packs
or publishes. The TypeScript package is published to [JSR](https://jsr.io) as
`@madduck/squoredata`, not to npmjs. npmjs is
unavailable to us, and GitHub Packages would force every consumer to hold a
GitHub account and a read token, even for a public package. JSR allows
anonymous installs and authenticates CI through OIDC, so no registry token is
stored as a secret.

The workflows are split by trigger, and the test jobs are defined once:

- `.github/workflows/_tests.yml` holds the test jobs and has no trigger of its
  own; it is a reusable workflow (`workflow_call`).
- `.github/workflows/0-testing.yml` calls it on every push, every pull request,
  and on manual dispatch.
- `.github/workflows/1-build-and-publish.yml` calls it on a `v*` tag, then
  builds the Python distributions and the TypeScript tarball in one job, and
  then runs three jobs in parallel: the GitHub Release, the PyPI upload, and
  the JSR publish. Every job after the tests `needs` the build, and all of them
  are tag-gated, so a manual run on a branch only tests and builds.

Because a release is only ever published from a `v*` tag, and because publishing
an existing version fails, no branch push can publish anything. Staleness of the
committed TypeScript bindings is caught by the test job, which regenerates them
and fails on any diff before the build is allowed to start.

To release by hand, from the tagged commit so the version is the tag itself:

```sh
python scripts/generate_ts.py
git diff --exit-code typescript/   # must be clean before publishing
python scripts/stamp_version.py v0.1.1
cd typescript && npx jsr publish --allow-dirty
```

The stamp step is what the workflow does automatically; do not commit its
output, because the committed manifests keep the placeholder.  The stamp dirties
the tree, so jsr needs `--allow-dirty` to publish it.

A manual publish needs a JSR token (`npx jsr publish` prompts for it); CI does
not. Publishing a version is irreversible, so run the full definition of done
first.

The build job also attaches the output of `npm pack` to the GitHub Release,
so a consumer without any registry account can install straight from the tag:

```sh
npm install https://github.com/madduck/squoredata/releases/download/v0.1.0/madduck-squoredata-0.1.0.tgz
```

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
- `tests/test_version.py` pins the release-tag to semver translation in
  `scripts/stamp_version.py`, including the tags that must raise, and checks
  that the generator writes the placeholder.

## TypeScript generation

The TypeScript package is `@madduck/squoredata`, published from `typescript/`.
The JSON Schema is the single source of truth: the interfaces and the runtime
validators are both derived from it.

- `scripts/generate_ts.py` uses `model_json_schema(mode="serialization")`, which
  is the wire format and therefore includes the computed fields.
- `scripts/generate_ts.py` also emits `typescript/jsr.json`, the JSR manifest.
  Like `typescript/package.json`, it always carries the placeholder version
  `0.0.0` and is never set by hand. Its `imports` map resolves the bare `ajv`
  specifier to `npm:ajv@^8.17.1`, because JSR does not resolve bare specifiers
  on its own.
- `scripts/stamp_version.py` turns a release tag into a valid semver and writes
  it into both manifests: `v0.1.1` becomes `0.1.1`. Anything that is not an
  exact `v<major>.<minor>.<patch>` tag raises, so a malformed tag fails the
  release rather than publishing a wrong version. The release workflow runs it
  before `npm pack` and before `jsr publish`.
- Stamping leaves the tree dirty, and `jsr publish` refuses a dirty tree. The
  publish step therefore passes `--allow-dirty`. Committing the stamp in the
  runner instead would attest provenance for a commit that exists nowhere, so
  the dirty stamp plus the real tag is the lesser evil.
- A per-commit version in the committed manifests would make them differ on
  every commit and turn the CI drift check below into a false positive that
  carries no information. That is why the version is release metadata stamped
  at publish time rather than part of the generated artefacts.
- `index.js` starts with `// @ts-self-types="./index.d.ts"`. JSR otherwise
  cannot tell that the declaration file describes the JavaScript entrypoint and
  warns about an untyped entrypoint.
- The generator writes `<Model>.schema.json` and `<Model>.d.ts` for json2ts's
  own use, plus the shippable artefacts: `schemas/<Model>.schema.json`,
  `index.js`, `index.d.ts`, `package.json`, `jsr.json`, and a copy of
  `LICENSE`.
- Because Pydantic emits no `$schema` key, the generator stamps
  `https://json-schema.org/draft/2020-12/schema` into every schema. Without it
  Ajv would fall back to draft-07 while the models follow draft 2020-12.
- The generated `package.json` and `jsr.json` are built from templates inside
  `generate_ts.py`; their `version` is derived from the Git tag, the same
  source `hatch-vcs` uses for the Python package, so the JSR and Python
  versions always mirror each other. The version is **not** set by hand.
- `index.js` compiles the schemas with Ajv
  (`ajv/dist/2020.js`) and exports `validateSquoreMatch`,
  `validateSquoreMatchLiveData`, and `schemas`.
- JSR has no `files` allowlist equivalent to npm's, so it publishes
  `typescript/tests/` along with the artefacts. That is harmless and is left
  alone rather than restructured.
- `index.d.ts` re-exports only the public interfaces with explicit
  `export type { X } from "./X"`. A plain `export *` collides, because
  `json-schema-to-typescript` emits dozens of helper type aliases (`A`, `B1`, …)
  into each file and the two model files share names.
- `Game.score` and the computed `scores` use a plain serializer that converts
  tuples to lists. Without it, json2ts loses the element typing and emits
  `[unknown, unknown]`.
- Regenerate with `python scripts/generate_ts.py` after any model change, and
  commit the output, including `jsr.json`.

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
  the models to render their schemas, and `hatch-vcs`, which resolves the
  dynamic version from the Git tag.
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
(cd typescript && npx jsr publish --dry-run --allow-dirty)
```

`npm test` runs both the type check (`tsc --noEmit`) and the runtime golden
tests (`node --test`). The JSR dry run catches a manifest or entrypoint problem
before a real, irreversible publish.

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
- Do not reintroduce a literal project version. The Git tag is the single
  source of truth; `pyproject.toml` keeps `dynamic = ["version"]`.
- Do not commit a stamped `typescript/package.json` or `typescript/jsr.json`.
  The committed manifests keep the placeholder; only the release stamps them.
- Do not let a build reach the network; the hook guards against this.
- Do not weaken the strict mypy settings or `extra="forbid"` to make something
  pass.
