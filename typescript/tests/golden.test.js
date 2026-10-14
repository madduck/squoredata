// Runtime golden test.  The compiled validators must accept the shared golden
// files and reject deliberate mismatches, so this test can actually fail.
//
//   node --test typescript/tests/golden.test.js
//
// The test imports the generated package entry point, so it also proves that
// index.js and the schema files resolve.
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

import {
  schemas,
  validateSquoreMatch,
  validateSquoreMatchLiveData,
} from "../index.js";

const GOLDEN = new URL("../../golden/", import.meta.url);

async function golden(name) {
  return JSON.parse(await readFile(new URL(name, GOLDEN), "utf8"));
}

test("golden squore-match.json validates", async () => {
  assert.equal(validateSquoreMatch(await golden("squore-match.json")), true);
});

test("golden squore-match-livedata.json validates", async () => {
  assert.equal(
    validateSquoreMatchLiveData(await golden("squore-match-livedata.json")),
    true,
  );
});

test("an extra property is rejected", async () => {
  const match = await golden("squore-match.json");
  match.unexpected = "nope";
  assert.equal(validateSquoreMatch(match), false);
});

test("a missing required property is rejected", async () => {
  const match = await golden("squore-match.json");
  delete match.players.B;
  assert.equal(validateSquoreMatch(match), false);
});

test("a wrong type is rejected", async () => {
  const match = await golden("squore-match.json");
  match.players.A = 42;
  assert.equal(validateSquoreMatch(match), false);
});

test("the schemas are exported as objects", () => {
  assert.equal(typeof schemas.SquoreMatch, "object");
  assert.equal(typeof schemas.SquoreMatchLiveData, "object");
  assert.equal(
    schemas.SquoreMatch.$schema,
    "https://json-schema.org/draft/2020-12/schema",
  );
});
