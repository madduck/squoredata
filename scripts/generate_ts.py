#!/usr/bin/env python3
"""Generate the TypeScript bindings, runtime validators, and package metadata.

The script renders the JSON Schema of each Pydantic model and converts it to
TypeScript with ``json-schema-to-typescript`` (``json2ts``).  It also emits the
runtime side of the npm package: an ``index.js`` that compiles each schema with
Ajv, an ``index.d.ts`` that re-exports the interfaces and the validator
signatures, a ``package.json``, and a copy of the licence.

The JSON Schema is the single source of truth.  The TypeScript interfaces and
the runtime validators are both derived from it, so they cannot disagree with
the Pydantic models or with each other.

Usage::

    python scripts/generate_ts.py

The generated files live under ``typescript/`` and are committed to the
repository.  The version of the npm package mirrors the Python package version
in ``pyproject.toml``.
"""

import json
import shutil
import subprocess  # nosec B404
import sys
import tomllib
from pathlib import Path

from pydantic import BaseModel

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "src"
TS_DIR = REPO_ROOT / "typescript"

sys.path.insert(0, str(SRC))

# Import after sys.path manipulation so the script works without installation.
from squoredata import SquoreMatch, SquoreMatchLiveData  # noqa: E402

MODELS: dict[str, type[BaseModel]] = {
    "SquoreMatch": SquoreMatch,
    "SquoreMatchLiveData": SquoreMatchLiveData,
}

NPM_PACKAGE_NAME = "@madduck/squoredata"
NPM_REPOSITORY = "git+https://github.com/madduck/squoredata.git"
NPM_HOMEPAGE = "https://github.com/madduck/squoredata#readme"
NPM_BUGS = "https://github.com/madduck/squoredata/issues"
NPM_DESCRIPTION = (
    "TypeScript bindings and JSON Schema validators for the squoredata Pydantic models"
)
# The only runtime dependency: the reference JSON Schema validator.
NPM_AJV_RANGE = "^8.17.1"


def _json2ts_command() -> list[str]:
    """Return the command to run json-schema-to-typescript.

    Prefer the locally installed binary, fall back to ``npx`` so the script is
    usable right after a fresh checkout.
    """
    local = REPO_ROOT / "node_modules" / ".bin" / "json2ts"
    if local.exists():
        return [str(local)]
    return ["npx", "--yes", "json-schema-to-typescript"]


def _version() -> str:
    """Return the project version, read from ``pyproject.toml``.

    The npm package version mirrors the Python package version, so that the two
    sides of the contract are always released together.
    """
    with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
        return str(tomllib.load(handle)["project"]["version"])


def _write_schemas() -> dict[str, Path]:
    """Write the JSON Schema for every model and return the paths.

    Each schema is written twice: once next to the generated interfaces, where
    json2ts consumes it, and once under ``schemas/`` as a stable, addressable
    copy that any language can fetch from the published package.
    """
    paths: dict[str, Path] = {}
    schemas_dir = TS_DIR / "schemas"
    schemas_dir.mkdir(parents=True, exist_ok=True)
    for name, model in MODELS.items():
        # The serialization schema is the wire format: it carries the computed
        # fields (status, games, scores, winner) that a consumer sees.  The
        # golden files are serialized instances, so they must match this schema.
        schema = model.model_json_schema(mode="serialization")
        # Pydantic emits no ``$schema`` key.  Without it Ajv would fall back to
        # draft-07, while Pydantic follows draft 2020-12.  Pin it explicitly so
        # the runtime validator and the models agree.
        schema = {"$schema": "https://json-schema.org/draft/2020-12/schema", **schema}
        rendered = json.dumps(schema, indent=2, sort_keys=True) + "\n"
        path = TS_DIR / f"{name}.schema.json"
        path.write_text(rendered, encoding="utf-8")
        (schemas_dir / f"{name}.schema.json").write_text(rendered, encoding="utf-8")
        paths[name] = path
    return paths


def _write_interfaces(schema_paths: dict[str, Path]) -> None:
    """Convert each JSON Schema into a TypeScript interface with json2ts."""
    cmd = _json2ts_command()
    # ``cmd`` is the local json2ts binary with a fixed argv, so B603 does not
    # apply.  The marker is line-scoped: subprocess use elsewhere still warns.
    for name, schema_path in schema_paths.items():
        subprocess.run(  # nosec B603
            [
                *cmd,
                "--input",
                str(schema_path),
                "--output",
                str(TS_DIR / f"{name}.d.ts"),
            ],
            check=True,
            cwd=REPO_ROOT,
        )


def _write_index_dts() -> None:
    """Write ``index.d.ts``: the public interfaces and validator signatures."""
    # A plain ``export *`` would collide: json2ts emits dozens of helper type
    # aliases (``A``, ``B1``, ...) into each file, and the two files share
    # names.  Export only the public interfaces instead.
    lines = ["// Generated by scripts/generate_ts.py. Do not edit by hand."]
    for name in MODELS:
        lines.append(f'export type {{ {name} }} from "./{name}";')
    lines.append("")
    lines.append(
        "export { schemas, validateSquoreMatch, validateSquoreMatchLiveData };"
    )
    lines.append("")
    lines.append("/** A validation error as reported by Ajv. */")
    lines.append("export interface ValidationError {")
    lines.append("  instancePath: string;")
    lines.append("  schemaPath: string;")
    lines.append("  keyword: string;")
    lines.append("  message?: string;")
    lines.append("}")
    lines.append("")
    lines.append("/** The result of validating an unknown value against a schema. */")
    lines.append("export interface ValidationResult {")
    lines.append("  valid: boolean;")
    lines.append("  errors: ValidationError[] | null;")
    lines.append("}")
    lines.append("")
    lines.append("/** Validate an unknown value as a ``SquoreMatch``. */")
    lines.append("export declare function validateSquoreMatch(")
    lines.append("  value: unknown,")
    lines.append("): value is SquoreMatch;")
    lines.append("")
    lines.append("/** Validate an unknown value as a ``SquoreMatchLiveData``. */")
    lines.append("export declare function validateSquoreMatchLiveData(")
    lines.append("  value: unknown,")
    lines.append("): value is SquoreMatchLiveData;")
    lines.append("")
    lines.append("/** The raw JSON Schema documents, as runtime objects. */")
    lines.append("export declare const schemas: {")
    for name in MODELS:
        lines.append(f"  {name}: Record<string, unknown>;")
    lines.append("};")
    (TS_DIR / "index.d.ts").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_index_js() -> None:
    """Write ``index.js``: Ajv-backed runtime validators and schema exports."""
    lines = [
        "// Generated by scripts/generate_ts.py. Do not edit by hand.",
        'import Ajv2020 from "ajv/dist/2020.js";',
    ]
    for name in MODELS:
        lines.append(
            f'import {name}Schema from "./schemas/{name}.schema.json" with '
            '{ type: "json" };'
        )
    lines.append("")
    lines.append("const ajv = new Ajv2020({")
    lines.append("  allErrors: true,")
    lines.append("  strict: false,")
    lines.append("  // Pydantic accepts datetimes that do not carry an offset, while")
    lines.append("  // Ajv's strict date-time regex does not.  Format checks would")
    lines.append("  // reject valid tablet data, so validation covers structure only:")
    lines.append("  // types, required properties, and forbidden extras.")
    lines.append("  validateFormats: false,")
    lines.append("});")
    lines.append("")
    for name in MODELS:
        lines.append(f"const {name}Compiled = ajv.compile({name}Schema);")
    lines.append("")
    lines.append("export const schemas = {")
    for name in MODELS:
        lines.append(f"  {name}: {name}Schema,")
    lines.append("};")
    lines.append("")
    for name in MODELS:
        lines.append(f"export function validate{name}(value) {{")
        lines.append(f"  return {name}Compiled(value);")
        lines.append("}")
        lines.append("")
    (TS_DIR / "index.js").write_text("\n".join(lines), encoding="utf-8")


def _write_package_json() -> None:
    """Write the npm ``package.json``, with the version taken from pyproject."""
    payload = {
        "name": NPM_PACKAGE_NAME,
        "version": _version(),
        "description": NPM_DESCRIPTION,
        "license": "MIT",
        "repository": {"type": "git", "url": NPM_REPOSITORY},
        "homepage": NPM_HOMEPAGE,
        "bugs": {"url": NPM_BUGS},
        "type": "module",
        "main": "./index.js",
        "types": "./index.d.ts",
        "exports": {
            ".": {
                "types": "./index.d.ts",
                "default": "./index.js",
            },
            "./schemas/SquoreMatch.schema.json": "./schemas/SquoreMatch.schema.json",
            "./schemas/SquoreMatchLiveData.schema.json": (
                "./schemas/SquoreMatchLiveData.schema.json"
            ),
            "./package.json": "./package.json",
        },
        "files": [
            "index.js",
            "index.d.ts",
            "*.d.ts",
            "schemas",
            "README.md",
            "LICENSE",
        ],
        "dependencies": {"ajv": NPM_AJV_RANGE},
        "keywords": [
            "squore",
            "squoredata",
            "pydantic",
            "json-schema",
            "typescript",
            "types",
        ],
        "sideEffects": False,
    }
    (TS_DIR / "package.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )


def _copy_license() -> None:
    """Copy the repository licence next to the generated package manifest."""
    shutil.copyfile(REPO_ROOT / "LICENSE", TS_DIR / "LICENSE")


def generate() -> None:
    """Write every generated artefact for the TypeScript package."""
    TS_DIR.mkdir(parents=True, exist_ok=True)
    schema_paths = _write_schemas()
    _write_interfaces(schema_paths)
    _write_index_dts()
    _write_index_js()
    _write_package_json()
    _copy_license()


if __name__ == "__main__":
    generate()
