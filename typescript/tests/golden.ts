// Golden test: the shared files in golden/ must satisfy the generated
// interfaces, and the runtime validators must accept them and reject
// deliberate mismatches.
//
//   node --test typescript/tests/golden.test.js   (runtime)
//   npx tsc --noEmit -p tsconfig.json             (types)
//
// A mismatch between the Pydantic models and the generated TypeScript makes
// this file fail to compile or fail to run.
import squoreMatch from "../../golden/squore-match.json";
import squoreMatchLiveData from "../../golden/squore-match-livedata.json";
import type { SquoreMatch } from "../SquoreMatch";
import type { SquoreMatchLiveData } from "../SquoreMatchLiveData";

export const goldenSquoreMatch: SquoreMatch = squoreMatch as SquoreMatch;
export const goldenSquoreMatchLiveData: SquoreMatchLiveData =
  squoreMatchLiveData as SquoreMatchLiveData;

// The computed fields must be part of the wire format and thus of the type.
export const status: number = goldenSquoreMatchLiveData.status;
export const games: unknown[] = goldenSquoreMatchLiveData.games;
export const scores: unknown[] = goldenSquoreMatchLiveData.scores;
export const matchid: string = goldenSquoreMatch.metadata.sourceID;
