"""Point-level data as used by Squore.

The types and the parser are ported from the ``tcboard`` project so that the
Squore data structures are self-contained.
"""

import re
from typing import Literal

from pydantic import BaseModel, TypeAdapter, ValidationError

__all__ = [
    "AppealType",
    "PlayerIndex",
    "PlayerLetter",
    "Point",
    "ServerSide",
    "make_point_from_squore_line",
]

type PlayerLetter = Literal["A"] | Literal["B"]
type PlayerIndex = Literal[0] | Literal[1]
type ServerSide = Literal["L"] | Literal["R"]
type AppealType = Literal["S"] | Literal["L"] | Literal["N"]


class Point(BaseModel):
    """A single point in a game."""

    server: PlayerIndex | None
    serveside: ServerSide | None
    player: PlayerIndex
    data: int | AppealType
    duration: int | None = None


PATTERN = re.compile(
    r"(?P<AX>(?P<AS>[-RL])(?P<AP>\d+|-)|ST|[YN]L)"
    r"(?P<BX>(?P<BS>[-RL])(?P<BP>\d+|-)|ST|[YN]L)",
)

type PointDataType = AppealType | int
PointDataTypeValidator: TypeAdapter[PointDataType] = TypeAdapter(PointDataType)
PlayerIndexValidator: TypeAdapter[PlayerIndex] = TypeAdapter(PlayerIndex)
PlayerLetterValidator: TypeAdapter[PlayerLetter] = TypeAdapter(PlayerLetter)
ServerSideValidator: TypeAdapter[ServerSide] = TypeAdapter(ServerSide)


def make_point_from_squore_line(
    squore: str | None, *, duration: int | None = None
) -> Point:
    """Parse a Squore line representation into a :class:`Point`.

    Args:
        squore: The Squore line representation, e.g. ``"R1--"``.
        duration: The optional duration of the point in seconds.

    Returns:
        The parsed point.

    Raises:
        ValueError: If the line cannot be parsed.
    """
    m = None
    if squore is not None:
        m = re.fullmatch(PATTERN, squore)

    if m is None:
        raise ValueError(f"Not a Squore line I can parse: {squore}")

    d = m.groupdict()

    winner = int((a := d["AX"]) == "--")  # bool to int: True→1, False→0
    server, side = None, None
    data: PointDataType
    match a, d["BX"]:
        case ("ST", _) | (_, "ST"):
            data = "S"
        case ("YL", _) | (_, "YL"):
            data = "L"
        case ("NL", _) | (_, "NL"):
            data = "N"
        case _:
            try:
                winner = PlayerIndexValidator.validate_python(
                    # bool to int: True→1, False→0
                    int(d["AP"] == "-")
                )
                server = PlayerIndexValidator.validate_python(
                    # bool to int: True→1, False→0
                    int(d["AS"] == "-")
                )
                side = ServerSideValidator.validate_python(
                    a if (a := d["AS"]) != "-" else d["BS"]
                )
                data = PointDataTypeValidator.validate_python(
                    a if (a := d["AP"]) != "-" else d["BP"]
                )

            except ValidationError as err:
                raise ValueError(f"Not a Squore line I can parse: {squore}") from err

    return Point(
        server=server,
        serveside=side,
        data=data,
        player=1 if winner else 0,
        duration=duration,
    )
