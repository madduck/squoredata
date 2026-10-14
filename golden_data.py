"""Canonical golden instances shared by the Python and TypeScript tests.

The values here are fixed (no ``datetime.now()``) so that the emitted JSON is
stable and can be committed under ``golden/``.
"""

from datetime import datetime, timedelta

from squoredata import (
    Event,
    Format,
    Metadata,
    Players,
    SquoreDeviceInfo,
    SquoreMatch,
    SquoreMatchLiveData,
    TimerInfo,
    Timing,
    When,
)

# 2024-01-02T03:04:05:06 with microseconds, so the ISO round-trip is exact.
NOW = datetime(2024, 1, 2, 3, 4, 5, 6)


def _players() -> Players:
    return Players(A="Jane Doe", B="Mary Major")


def _event() -> Event:
    return Event(name="Golden Tournament", division="Court 1")


def _format() -> Format:
    return Format(
        numberOfPointsToWinGame=11,
        numberOfGamesToWinMatch=3,
        useHandInHandOutScoring=False,
    )


def _device() -> SquoreDeviceInfo:
    return SquoreDeviceInfo(
        batteryCharging=True,
        batteryPercentage=42,
        deviceid="squore-golden",
        timestamp=NOW,
    )


def _metadata() -> Metadata:
    return Metadata(sourceID="golden-match", device=_device())


def _timing(*games: tuple[int, int]) -> list[Timing]:
    timing: list[Timing] = []
    endtime = NOW
    for a, b in reversed(games):
        starttime = endtime - timedelta(seconds=a + b)
        timing.append(
            Timing(
                start=starttime.isoformat(),
                end=endtime.isoformat(),
                offsets=list(range(1, a + b + 1)),
            )
        )
        endtime = starttime - timedelta(seconds=90)
    return timing[::-1]


def _scorelines(*games: tuple[int, int]) -> list[list[str]]:
    ret: list[list[str]] = []
    for a, b in games:
        line: list[str] = []
        for i in range(max(a, b)):
            if i < a:
                line.append(f"L{i + 1}--")
            if i < b:
                line.append(f"R--{i + 1}")
        ret.append(line)
    return ret


GAMES: tuple[tuple[int, int], ...] = ((11, 9), (11, 7), (4, 6))


def squash_golden_match() -> SquoreMatch:
    """Return the canonical :class:`SquoreMatch` golden instance."""
    return SquoreMatch(
        players=_players(),
        countries=None,
        clubs=None,
        colors=None,
        event=_event(),
        format=_format(),
        metadata=_metadata(),
    )


def golden_match_livedata() -> SquoreMatchLiveData:
    """Return the canonical :class:`SquoreMatchLiveData` golden instance."""
    return SquoreMatchLiveData(
        players=_players(),
        event=_event(),
        format=_format(),
        metadata=_metadata(),
        court=1,
        timestamp=NOW,
        appName="Squore",
        appPackage="com.doubleyellow.scoreboard",
        isGameBall=True,
        isHandOut=True,
        isMatchBall=False,
        isVictoryFor=None,
        isUndo=False,
        liveScoreDeviceId="squore-golden",
        lockState="Unlocked",
        result="2-1",
        gamescores="11-9,11-7,4-6",
        score=_scorelines(*GAMES),
        server="A",
        serveSide="R",
        start=NOW.isoformat(),
        timerInfo=TimerInfo(type="UntilStartOfNextGame", totalSeconds=15),
        timing=_timing(*GAMES),
        when=When(date=NOW.date().isoformat(), time=NOW.time().isoformat()),
    )


GOLDEN: dict[str, object] = {
    "squore-match.json": squash_golden_match,
    "squore-match-livedata.json": golden_match_livedata,
}
