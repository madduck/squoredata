"""Live match data as reported by a Squore tablet."""

import itertools
from datetime import datetime
from typing import Any, Literal, Never

from pydantic import (
    BaseModel,
    Field,
    computed_field,
    field_serializer,
    field_validator,
)

from .game import Game, ScoresType
from .livestatus import LiveStatus
from .match import SquoreMatch
from .point import PlayerLetter, Point, ServerSide, make_point_from_squore_line

type ServerType = PlayerLetter
type LockStateType = (  # src/com/doubleyellow/scoreboard/model/LockState.java
    Literal["Unlocked"]
    | Literal["UnlockedManual"]
    | Literal["UnlockedEndOfFinalGame"]
    | Literal["LockedManual"]
    | Literal["LockedManualGUI"]
    | Literal["LockedEndOfMatch"]
    | Literal["LockedIdleTime"]
    | Literal["SharedEndedMatch"]
    | Literal["LockedEndOfMatchRetired"]
    | Literal["LockedEndOfMatchConduct"]
    | Literal["LockedEndOfMatchTimeBased"]
    | None
)


class InconsistentStateError(Exception):
    """The Squore state is internally inconsistent."""

    def __init__(self, matchid: str, deviceid: str) -> None:
        super().__init__(
            f"Inconsistent Squore state (bug #120), matchid={matchid}, "
            f"deviceid={deviceid}"
        )
        self.matchid = matchid
        self.deviceid = deviceid


class When(BaseModel, extra="forbid"):
    """The date and time a match is scheduled for."""

    date: str
    time: str


class Timing(BaseModel, extra="forbid"):
    """Timing information for one game."""

    start: str
    end: str
    offsets: list[int] | None = None


class TimerInfo(BaseModel, extra="forbid"):
    """Information about a running countdown timer."""

    type: (
        Literal["Warmup"]
        | Literal["UntilStartOfFirstGame"]
        | Literal["UntilStartOfNextGame"]
    )
    totalSeconds: int


class SquoreMatchLiveData(SquoreMatch, extra="forbid"):
    """A Squore match together with the live data reported by the tablet."""

    appName: Literal["Squore"]
    appPackage: Literal["com.doubleyellow.scoreboard"]
    court: int | None
    timestamp: datetime | None = None
    customData: dict[str, Any] | None = None
    gamescores: str | None = None
    isGameBall: bool
    isHandOut: bool
    isMatchBall: bool
    isVictoryFor: PlayerLetter | None = None
    isUndo: bool = False
    lastCall: str | None = None
    lastScorer: PlayerLetter | None = None
    liveScoreDeviceId: str
    lockState: LockStateType = None
    maxNrOfPowerPlays: int | None = None
    result: str
    score: list[list[str]] = Field(default_factory=list[list[str]])
    server: ServerType
    serveSide: ServerSide
    start: str
    timerInfo: TimerInfo | None = None
    timing: list[Timing] = Field(default_factory=list[Timing])
    when: When

    def model_post_init(self, ctx: Any) -> None:
        if self.timestamp is None:
            self.timestamp = (ctx or {}).get("timestamp") or datetime.now()

    @property
    def matchid(self) -> str:
        return self.metadata.sourceID

    @computed_field  # type: ignore[prop-decorator]
    @property
    def status(self) -> LiveStatus:
        if self.timerInfo:
            if self.timerInfo.type == "Warmup":
                return LiveStatus.WARMUP

            if self.timerInfo.type == "UntilStartOfFirstGame":
                return LiveStatus.PREPARE

            elif self.timerInfo.totalSeconds == 15:
                return LiveStatus.FIFTEENSECONDS

            return LiveStatus.BETWEENGAMES

        elif self.score:
            if self.isMatchBall:
                return LiveStatus.MATCHBALL

            elif self.isGameBall:
                return LiveStatus.GAMEBALL

            elif self.isVictoryFor:
                return LiveStatus.FINISHED

            return LiveStatus.ONGOING

        return LiveStatus.READY

    def nr_games_played(self) -> int:
        return sum(int(x) for x in self.result.split("-"))

    @computed_field  # type: ignore[prop-decorator]
    @property
    def scores(self) -> ScoresType:
        if self.gamescores is None:
            return []

        ret = []
        for gscore in self.gamescores.split(","):
            ret.append((int((s := gscore.split("-"))[0]), int(s[1])))
        return ret

    @field_serializer("scores", mode="plain")
    def _scores_as_lists(self, value: ScoresType) -> list[list[int]]:
        # Convert the tuples to lists for the schema, because otherwise json2ts
        # loses the element typing and emits [unknown, unknown].
        return [list(game) for game in value]

    def _get_scoreline(
        self, scores: list[str], offsets: list[int] | None
    ) -> list[Point]:
        ret: list[Point] = []

        prev_offset = 0
        for point, offset in itertools.zip_longest(scores, offsets or []):
            ret.append(
                make_point_from_squore_line(point, duration=offset - prev_offset)
            )
            prev_offset = offset

        return ret

    @computed_field  # type: ignore[prop-decorator]
    @property
    def games(self) -> list[Game]:
        nr_games_played = self.nr_games_played()
        ret = []

        is_cur = False
        for i, ((a, b), points, timings) in enumerate(
            zip(
                self.scores,
                self.score,
                [t for t in self.timing if t.offsets is not None],
                strict=True,
            )
        ):
            scoreline = self._get_scoreline(points, timings.offsets)

            is_cur = i == nr_games_played
            ret.append(
                Game(
                    score=(a, b),
                    starttime=datetime.fromisoformat(timings.start),
                    endtime=None if is_cur else datetime.fromisoformat(timings.end),
                    winner=None if is_cur else int(a < b),
                    scoreline=scoreline,
                )
            )

        if (
            not is_cur
            and self.status >= LiveStatus.READY
            and self.status < LiveStatus.FINISHED
        ) or (
            len(self.timing) == 1
            and self.timing[0].offsets is None
            and self.score == []
        ):
            ret.append(Game(score=(0, 0)))
        return ret

    @computed_field  # type: ignore[prop-decorator]
    @property
    def winner(self) -> int | None:
        if self.isVictoryFor is None:
            return None
        return {"A": 0, "B": 1}[self.isVictoryFor]

    def validate_livedata(self) -> Never | None:
        if len([t for t in self.timing if t.offsets is not None]) != len(self.scores):
            raise InconsistentStateError(
                matchid=self.matchid, deviceid=self.liveScoreDeviceId
            )
        return None

    @field_validator("court", mode="before")
    @classmethod
    def handle_no_court_as_string(
        cls, data: Literal["null"] | int | None
    ) -> int | None:
        return None if data == "null" else data
