"""The static Squore match description, i.e. a match without live data."""

from typing import Literal

from pydantic import BaseModel

from .devinfo import SquoreDeviceInfo


class Players(BaseModel, extra="forbid"):
    """The names of the two players."""

    A: str
    B: str


class PlayersProps(BaseModel, extra="forbid"):
    """A per-player attribute, one value for each player."""

    A: str | None = None
    B: str | None = None


class Colors(PlayersProps): ...


class Countries(PlayersProps): ...


class Clubs(PlayersProps): ...


class Event(BaseModel, extra="forbid"):
    """The event a match belongs to."""

    name: str
    division: str


class Format(BaseModel, extra="forbid"):
    """The scoring format of a match."""

    numberOfPointsToWinGame: int = 11
    numberOfGamesToWinMatch: int = 3
    useHandInHandOutScoring: bool = False


class Wifi(BaseModel, extra="forbid"):
    """The WiFi details a device is connected to."""

    ipaddress: str | None = None
    ssid: str | None = None


class Metadata(BaseModel, extra="forbid"):
    """Metadata a Squore tablet attaches to a match."""

    sourceID: str
    device: SquoreDeviceInfo | None = None
    source: str | None = None
    version: int | None = None
    language: str | None = None
    wifi: Wifi | None = None
    shareURL: str | None = None
    sourceFeedbackState: (
        Literal["SourceAcceptedFinalResult"] | Literal["SourceRejectedResult"] | None
    ) = None
    sourcePostResultUrl: str | None = None


class SquoreMatch(BaseModel, extra="forbid"):
    """A match as used by Squore, without any live information."""

    players: Players
    clubs: Clubs | None = None
    colors: Colors | None = None
    countries: Countries | None = None
    event: Event
    format: Format
    metadata: Metadata

    @property
    def matchid(self) -> str:
        return self.metadata.sourceID
