from __future__ import annotations

from typing_extensions import NotRequired, TypedDict

from league_ranker import LeaguePoints

from sr.comp.scores import LeaguePosition
from sr.comp.types import GamePoints


class NameWithURL(TypedDict):

    name: str
    get: str


class TeamScores(TypedDict):

    league: LeaguePoints
    game: GamePoints


class TeamInfo(TypedDict):

    name: str
    get: str
    tla: str
    league_pos: LeaguePosition
    location: NameWithURL
    scores: TeamScores
    image_url: NotRequired[str]
