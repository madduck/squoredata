import pytest

from squoredata import LiveStatus


@pytest.mark.parametrize(
    "status, expected",
    [
        (LiveStatus.UNKNOWN, "???"),
        (LiveStatus.WARMUP, "WUP"),
        (LiveStatus.PREPARE, "PRE"),
        (LiveStatus.READY, "RDY"),
        (LiveStatus.ONGOING, "ONG"),
        (LiveStatus.GAMEBALL, "GBL"),
        (LiveStatus.BETWEENGAMES, "PAU"),
        (LiveStatus.FIFTEENSECONDS, "15s"),
        (LiveStatus.MATCHBALL, "MBL"),
        (LiveStatus.FINISHED, "FIN"),
        (LiveStatus.EXTERNAL, "EXT"),
    ],
)
def test_short(status: LiveStatus, expected: str) -> None:
    assert status.short == expected


def test_str_is_name() -> None:
    assert str(LiveStatus.ONGOING) == "ONGOING"


@pytest.mark.parametrize(
    "new, old, expected",
    [
        (LiveStatus.UNKNOWN, LiveStatus.UNKNOWN, False),
        (LiveStatus.WARMUP, LiveStatus.FINISHED, False),
        (LiveStatus.ONGOING, LiveStatus.BETWEENGAMES, True),
        (LiveStatus.ONGOING, LiveStatus.GAMEBALL, True),
        (LiveStatus.ONGOING, LiveStatus.MATCHBALL, True),
        (LiveStatus.ONGOING, LiveStatus.FIFTEENSECONDS, True),
        (LiveStatus.FIFTEENSECONDS, LiveStatus.GAMEBALL, True),
        (LiveStatus.FIFTEENSECONDS, LiveStatus.PREPARE, True),
        (LiveStatus.FINISHED, LiveStatus.BETWEENGAMES, True),
        (LiveStatus.READY, LiveStatus.FINISHED, False),
    ],
)
def test_can_come_after(new: LiveStatus, old: LiveStatus, expected: bool) -> None:
    assert new.can_come_after(old) is expected
