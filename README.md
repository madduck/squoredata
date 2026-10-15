# squoredata

Self-contained [Pydantic](https://docs.pydantic.dev) v2 data structures used by
[Squore](https://github.com/obbimi/Squore) scoreboard tablets.

The package was extracted from [`tcboard`](https://github.com/madduck/tcboard).
It contains only the data models, not the surrounding server logic. TypeScript
bindings are generated from the models so that a JavaScript or TypeScript
project can consume the same shape.

## Models

- `SquoreMatch` — a match as used by Squore, without any live information.
- `SquoreMatchLiveData` — a `SquoreMatch` together with the live data a tablet
  reports. It adds the `court` and `timestamp` fields.

Supporting models: `Players`, `Colors`, `Countries`, `Clubs`, `Event`, `Format`,
`Wifi`, `Metadata`, `SquoreDeviceInfo`, `TimerInfo`, `Timing`, `When`, `Point`,
`Game`, and the `LiveStatus` enum.

## Install

```sh
pip install squoredata
```

## TypeScript bindings

`scripts/generate_ts.py` renders the JSON Schema of each model and converts it
to TypeScript with
[`json-schema-to-typescript`](https://www.npmjs.com/package/json-schema-to-typescript).
The output lives in `typescript/` and is committed. The JSON Schema is the
single source of truth: the interfaces and the runtime validators are both
derived from it.

The npm package is published as `@madduck/squoredata`. It ships:

- `SquoreMatch.d.ts`, `SquoreMatchLiveData.d.ts` — the interfaces
- `index.js`, `index.d.ts` — Ajv-backed validators and the `schemas` object
- `schemas/*.schema.json` — the schema documents, addressable on their own

The package version mirrors the Python version, so the generator reads
`pyproject.toml` and writes the version into `typescript/package.json`.

The Hatch build hook (`hatch_build.py`) runs the generator before a wheel is
built, so a release can never carry stale bindings.

Install the generated package into another project from a published release,
or from the local directory:

```sh
npx jsr add @madduck/squoredata
npm install /path/to/squoredata/typescript
```

### Publishing

The TypeScript package is published to [JSR](https://jsr.io) as
`@madduck/squoredata`, by the tag-triggered workflow in
`.github/workflows/1-build-and-publish.yml`. JSR authenticates the workflow
through OIDC, so no registry token is stored as a secret.

First-time setup: claim the `@madduck` scope at <https://jsr.io/new> and link
it to the GitHub account that owns this repository.

To release by hand, with the version taken from `pyproject.toml`:

```sh
python scripts/generate_ts.py
git diff --exit-code typescript/   # must be clean before publishing
cd typescript && npx jsr publish
```

A local publish needs a JSR token; CI does not. Publishing a version that
already exists fails, so always release from a tag.

### Installing

JSR packages install into a Node project without an npmjs account. In a Node
project, use the JSR CLI:

```sh
npx jsr add @madduck/squoredata
```

For Deno, `deno add jsr:@madduck/squoredata` works directly.

The release workflow also attaches the packed tarball to the GitHub Release.
That route needs no registry and no account at all:

```sh
npm install https://github.com/madduck/squoredata/releases/download/v0.1.0/madduck-squoredata-0.1.0.tgz
```

The tarball has no version range and does not update, so prefer JSR unless you
need a fully offline or account-free install.

## Golden tests

The files in `golden/` are the shared contract between the two sides:

- `tests/test_golden.py` serialises and re-validates the models against the
  golden JSON.
- `typescript/tests/golden.ts` assigns the same JSON to the generated
  interfaces, so `tsc --noEmit` fails when the two sides diverge.
- `typescript/tests/golden.test.js` runs the generated validators against the
  same JSON, and asserts that they reject an extra property, a missing required
  property, and a wrong type.

Regenerate the golden files with `python scripts/make_golden.py` after a model
change.

## Development

```sh
pip install -e .[dev]
ruff check .
pytest
mypy --strict .

npm install
npm test
```
