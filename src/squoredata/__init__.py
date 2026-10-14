"""Self-contained Squore data structures.

This package encapsulates the data structures that a Squore tablet uses, as
opposed to the surrounding server logic in the ``tcboard`` project.
"""

from .devinfo import BatteryStatus, DeviceInfo, SquoreDeviceInfo
from .game import Game, Result, ScoresType, ScoreType
from .livedata import (
    InconsistentStateError,
    LockStateType,
    ServerType,
    SquoreMatchLiveData,
    TimerInfo,
    Timing,
    When,
)
from .livestatus import LiveStatus
from .match import (
    Clubs,
    Colors,
    Countries,
    Event,
    Format,
    Metadata,
    Players,
    PlayersProps,
    SquoreMatch,
    Wifi,
)
from .point import (
    AppealType,
    PlayerIndex,
    PlayerLetter,
    Point,
    ServerSide,
    make_point_from_squore_line,
)

__all__ = [
    "AppealType",
    "BatteryStatus",
    "Clubs",
    "Colors",
    "Countries",
    "DeviceInfo",
    "Event",
    "Format",
    "Game",
    "InconsistentStateError",
    "LiveStatus",
    "LockStateType",
    "Metadata",
    "PlayerIndex",
    "PlayerLetter",
    "Players",
    "PlayersProps",
    "Point",
    "Result",
    "ScoreType",
    "ScoresType",
    "ServerSide",
    "ServerType",
    "SquoreDeviceInfo",
    "SquoreMatch",
    "SquoreMatchLiveData",
    "TimerInfo",
    "Timing",
    "When",
    "Wifi",
    "make_point_from_squore_line",
]
