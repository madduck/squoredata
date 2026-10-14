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
The output lives in `typescript/` and is committed:

- `SquoreMatch.d.ts`, `SquoreMatchLiveData.d.ts` — the interfaces
- `SquoreMatch.schema.json`, `SquoreMatchLiveData.schema.json` — the schemata
- `index.d.ts` — re-exports

The Hatch build hook (`hatch_build.py`) runs the generator before a wheel is
built, so a release can never carry stale bindings.

Install the generated bindings into another project from the `typescript/`
directory, or from a published `squoredata-types` package:

```sh
npm install /path/to/squoredata/typescript
```

## Golden tests

The files in `golden/` are the shared contract between the two sides:

- `tests/test_golden.py` serialises and re-validates the models against the
  golden JSON.
- `typescript/tests/golden.ts` assigns the same JSON to the generated
  interfaces, so `tsc --noEmit` fails when the two sides diverge.

Regenerate the golden files with `python scripts/make_golden.py` after a model
change.

## Development

```sh
pip install -e .[dev]
ruff check .
pytest
mypy --strict .

npm install
node_modules/.bin/tsc --noEmit -p tsconfig.json
```
