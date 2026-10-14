import warnings
from datetime import datetime

import pytest
from conftest import LiveDataFactoryType

from squoredata import (
    Game,
    InconsistentStateError,
    LiveStatus,
    PlayerIndex,
    SquoreMatchLiveData,
    TimerInfo,
    Timing,
)


def test_match_court_nullstring_to_none(LiveDataFactory: LiveDataFactoryType) -> None:
    # https://github.com/obbimi/Squore/issues/96
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        bad_model_dump = LiveDataFactory(court="null").model_dump(
            exclude_computed_fields=True
        )
    assert SquoreMatchLiveData.model_validate(bad_model_dump).court is None


def test_match_warmup(
    LiveDataFactory: LiveDataFactoryType, timerinfo_warmup: TimerInfo
) -> None:
    assert LiveDataFactory(timerInfo=timerinfo_warmup).status == LiveStatus.WARMUP


def test_match_prepare(
    LiveDataFactory: LiveDataFactoryType, timerinfo_prepare: TimerInfo
) -> None:
    assert LiveDataFactory(timerInfo=timerinfo_prepare).status == LiveStatus.PREPARE


def test_match_prep15(
    LiveDataFactory: LiveDataFactoryType, timerinfo_15seconds: TimerInfo
) -> None:
    assert (
        LiveDataFactory(timerInfo=timerinfo_15seconds).status
        == LiveStatus.FIFTEENSECONDS
    )


def test_match_ready(LiveDataFactory: LiveDataFactoryType) -> None:
    assert LiveDataFactory().status == LiveStatus.READY


def test_match_ongoing(
    LiveDataFactory: LiveDataFactoryType, livedata_match_ongoing: SquoreMatchLiveData
) -> None:
    assert LiveDataFactory(base=livedata_match_ongoing).status == LiveStatus.ONGOING


def test_match_betweengames(
    LiveDataFactory: LiveDataFactoryType,
    livedata_match_ongoing: SquoreMatchLiveData,
    timerinfo_beforegame: TimerInfo,
) -> None:
    assert (
        LiveDataFactory(
            base=livedata_match_ongoing, timerInfo=timerinfo_beforegame
        ).status
        == LiveStatus.BETWEENGAMES
    )


def test_match_15seconds(
    LiveDataFactory: LiveDataFactoryType,
    livedata_match_ongoing: SquoreMatchLiveData,
    timerinfo_15seconds: TimerInfo,
) -> None:
    assert (
        LiveDataFactory(
            base=livedata_match_ongoing, timerInfo=timerinfo_15seconds
        ).status
        == LiveStatus.FIFTEENSECONDS
    )


def test_match_gameball(
    LiveDataFactory: LiveDataFactoryType, livedata_match_ongoing: SquoreMatchLiveData
) -> None:
    assert (
        LiveDataFactory(base=livedata_match_ongoing, isGameBall=True).status
        == LiveStatus.GAMEBALL
    )


def test_match_matchball(
    LiveDataFactory: LiveDataFactoryType, livedata_match_ongoing: SquoreMatchLiveData
) -> None:
    assert (
        LiveDataFactory(base=livedata_match_ongoing, isMatchBall=True).status
        == LiveStatus.MATCHBALL
    )


def test_match_finished(
    LiveDataFactory: LiveDataFactoryType, livedata_match_ongoing: SquoreMatchLiveData
) -> None:
    assert (
        LiveDataFactory(base=livedata_match_ongoing, isVictoryFor="A").status
        == LiveStatus.FINISHED
    )


@pytest.mark.parametrize(
    "inp, out",
    [("A", 0), ("B", 1), (None, None)],
)
def test_winner_accessor(
    inp: str | None,
    out: PlayerIndex | None,
    LiveDataFactory: LiveDataFactoryType,
) -> None:
    assert LiveDataFactory(isVictoryFor=inp).winner == out


def test_nr_games_finished(livedata_match_finished: SquoreMatchLiveData) -> None:
    assert livedata_match_finished.nr_games_played() == 5


def test_nr_games_ongoing(livedata_match_ongoing: SquoreMatchLiveData) -> None:
    assert livedata_match_ongoing.nr_games_played() == 2


def test_scores_base(livedata_match_base: SquoreMatchLiveData) -> None:
    assert livedata_match_base.scores == []


def test_scores_warmup(livedata_match_warmup: SquoreMatchLiveData) -> None:
    assert livedata_match_warmup.scores == []


def test_scores_ongoing(livedata_match_ongoing: SquoreMatchLiveData) -> None:
    assert livedata_match_ongoing.scores == [(11, 9), (11, 7), (4, 6)]


def test_scores_finished(livedata_match_finished: SquoreMatchLiveData) -> None:
    assert livedata_match_finished.scores == [
        (11, 9),
        (11, 7),
        (10, 12),
        (3, 11),
        (11, 13),
    ]


def test_games_base(livedata_match_base: SquoreMatchLiveData) -> None:
    assert livedata_match_base.games == [Game(score=(0, 0))]


def test_games_warmup(livedata_match_warmup: SquoreMatchLiveData) -> None:
    assert livedata_match_warmup.games == []


def test_games_ongoing(livedata_match_ongoing: SquoreMatchLiveData) -> None:
    assert len(livedata_match_ongoing.games) == 3


def test_games_finished(livedata_match_finished: SquoreMatchLiveData) -> None:
    assert len(livedata_match_finished.games) == 5


def test_validate_base(livedata_match_base: SquoreMatchLiveData) -> None:
    livedata_match_base.validate_livedata()


def test_validate_warmup(livedata_match_warmup: SquoreMatchLiveData) -> None:
    livedata_match_warmup.validate_livedata()


def test_validate_ongoing(livedata_match_ongoing: SquoreMatchLiveData) -> None:
    livedata_match_ongoing.validate_livedata()


def test_validate_finished(livedata_match_finished: SquoreMatchLiveData) -> None:
    livedata_match_finished.validate_livedata()


def test_validate_squore_bug_120(
    livedata_match_finished: SquoreMatchLiveData, now: datetime
) -> None:
    livedata_match_finished.timing.append(
        Timing(start=now.isoformat(), end=now.isoformat(), offsets=[])
    )
    with pytest.raises(InconsistentStateError):
        livedata_match_finished.validate_livedata()
