import pytest
from pydantic import ValidationError

from squoredata import Event, Format, Metadata, Players, SquoreMatch


def test_matchid_comes_from_metadata() -> None:
    sqmatch = SquoreMatch(
        players=Players(A="Jane", B="Mary"),
        event=Event(name="Tournament!", division="Division!"),
        format=Format(),
        metadata=Metadata(sourceID="matchid"),
    )
    assert sqmatch.matchid is sqmatch.metadata.sourceID


def test_match_is_strict_about_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        Metadata.model_validate({"sourceID": "matchid", "unknown": "value"})
