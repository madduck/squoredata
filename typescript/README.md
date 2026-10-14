# @madduck/squoredata

TypeScript bindings and JSON Schema validators for the
[`squoredata`](https://github.com/madduck/squoredata) Pydantic models.

The package gives a JavaScript or TypeScript project the same view of the data
that the Python server uses:

- **TypeScript interfaces** for `SquoreMatch` and `SquoreMatchLiveData`.
- **Runtime validators**, backed by [Ajv](https://ajv.js.org), that check an
  unknown value against the same rules the Python models enforce. Extra
  properties are rejected, because the models use `extra="forbid"`.
- **JSON Schema documents**, addressable on their own, for any other language
  or tool.

Everything is generated from the Pydantic models. This package and the Python
package always carry the same version.

## Install

```sh
npm install @madduck/squoredata
```

## Use the types

```ts
import type { SquoreMatchLiveData } from "@madduck/squoredata";

const match = (await response.json()) as SquoreMatchLiveData;
```

## Validate at runtime

Both validators narrow an `unknown` value, so the compiler knows the type after
the check.

```ts
import { validateSquoreMatchLiveData } from "@madduck/squoredata";

const payload: unknown = JSON.parse(body);

if (validateSquoreMatchLiveData(payload)) {
  // payload is SquoreMatchLiveData
  console.log(payload.event.name);
} else {
  console.error("invalid match");
}
```

To read the validation errors, compile the schema with Ajv yourself:

```ts
import Ajv from "ajv/dist/2020.js";
import { schemas } from "@madduck/squoredata";

const ajv = new Ajv({ allErrors: true, strict: false, validateFormats: false });
const validate = ajv.compile(schemas.SquoreMatchLiveData);

if (!validate(payload)) {
  console.error(validate.errors);
}
```

## Use the JSON Schema

The schema documents ship as JSON and are addressable by their own subpath.
Read them from JavaScript, from Python, or from any tool that understands JSON
Schema:

```js
import schema from "@madduck/squoredata/schemas/SquoreMatch.schema.json"
  with { type: "json" };
```

```python
import json, pathlib

schema = json.loads(
    pathlib.Path(
        "node_modules/@madduck/squoredata/schemas/SquoreMatch.schema.json"
    ).read_text()
)
```

## Validation scope

The validators check the structure of a value: types, required properties, and
forbidden extra properties. They do **not** check formats such as `date-time`.

The Python models accept timestamps without a UTC offset, but Ajv's strict
`date-time` pattern rejects them. Enforcing the format would therefore reject
valid data on the TypeScript side while Python accepts it. Structure is where
the two sides must agree, so that is what the validators check.

## What is in the package

| Path | Contents |
| --- | --- |
| `index.d.ts` | Interfaces, validator signatures, `schemas` object |
| `index.js` | The Ajv-backed validators and the schema objects |
| `SquoreMatch.d.ts`, `SquoreMatchLiveData.d.ts` | The interfaces |
| `schemas/*.schema.json` | The JSON Schema documents |

## Licence

MIT. See `LICENSE`.
