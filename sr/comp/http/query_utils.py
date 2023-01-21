"""Various utils for working with HTTP."""

from __future__ import annotations

import datetime
from typing import Callable, Mapping, overload, TypeVar, Union
from typing_extensions import TypedDict

from league_ranker import LeaguePoints, RankedPosition

from sr.comp.comp import SRComp
from sr.comp.match_period import Match, MatchType
from sr.comp.scores import BaseScores, degroup, Scores
from sr.comp.types import (
    ArenaName,
    GamePoints,
    MatchId,
    MatchNumber,
    ShepherdName,
    TLA,
)


class LeagueMatchScore(TypedDict):
    game: Mapping[TLA, GamePoints]
    league: Mapping[TLA, LeaguePoints]
    ranking: Mapping[TLA, RankedPosition]


class KnockoutMatchScore(TypedDict):
    game: Mapping[TLA, GamePoints]
    normalised: Mapping[TLA, LeaguePoints]
    ranking: Mapping[TLA, RankedPosition]


MatchScore = Union[LeagueMatchScore, KnockoutMatchScore]


class Times(TypedDict):
    start: str
    end: str


class StagingTimes(TypedDict):
    opens: str
    closes: str
    signal_teams: str
    signal_shepherds: dict[ShepherdName, str]


class MatchTimings(TypedDict):
    slot: Times
    game: Times
    staging: StagingTimes


class _MatchInfo(TypedDict):
    num: MatchNumber
    display_name: str
    arena: ArenaName
    teams: list[TLA | None]
    type: str  # noqa:A003
    times: MatchTimings


class MatchInfo(_MatchInfo, total=False):
    scores: MatchScore


TParseable = TypeVar('TParseable', int, str, datetime.datetime)


def get_scores(scores: Scores, match: Match) -> MatchScore | None:
    """
    Get a scores object suitable for JSON output.

    Parameters
    ----------
    scores : sr.comp.scores.Scores
        The competition scores.
    match : sr.comp.match_period.Match
        A match.

    Returns
    -------
    dict
        A dictionary suitable for JSON output.
    """
    k = (match.arena, match.num)

    def get_scores_info(match: Match) -> Union[
        tuple[BaseScores, Callable[[MatchId], dict[TLA, RankedPosition]]],
        tuple[None, None],
    ]:
        if match.type == MatchType.knockout:
            scores_info = scores.knockout
            if match.use_resolved_ranking:
                return scores_info, scores_info.resolved_positions.__getitem__
            # Just the Finals
            return scores_info, lambda k: degroup(scores_info.game_positions[k])

        elif match.type == MatchType.tiebreaker:
            scores_info = scores.tiebreaker
            return scores_info, \
                lambda k: degroup(scores_info.game_positions[k])

        else:
            return None, None

    scores_info, ranking = get_scores_info(match)
    if scores_info and ranking and k in scores_info.game_points:
        return {
            'game': scores_info.game_points[k],
            'normalised': scores_info.ranked_points[k],
            'ranking': ranking(k),
        }

    # TODO: consider using 'normalised' for both, instead of 'league' below
    league = scores.league
    if k in league.game_points:
        return {
            'game': league.game_points[k],
            'league': league.ranked_points[k],
            'ranking': degroup(league.game_positions[k]),
        }

    return None


def match_json_info(comp: SRComp, match: Match) -> MatchInfo:
    """
    Get match JSON information.

    Parameters
    ----------
    comp : sr.comp.comp.SRComp
        A competition instance.
    match : sr.comp.match_periods.Match
        A match.

    Returns
    -------
    dict
        A :class:`dict` containing JSON suitable output.
    """
    match_slot_lengths = comp.schedule.match_slot_lengths
    staging_times = comp.schedule.get_staging_times(match)

    info = MatchInfo({
        'num': match.num,
        'display_name': match.display_name,
        'arena': match.arena,
        'teams': match.teams,
        'type': match.type.value,
        'times': {
            'slot': {
                'start': match.start_time.isoformat(),
                'end': match.end_time.isoformat(),
            },
            'game': {
                'start': (
                    match.start_time +
                    match_slot_lengths['pre']
                ).isoformat(),
                'end': (
                    match.start_time +
                    match_slot_lengths['pre'] +
                    match_slot_lengths['match']
                ).isoformat(),
            },
            'staging': {
                'opens': staging_times['opens'].isoformat(),
                'closes': staging_times['closes'].isoformat(),
                'signal_teams': staging_times['signal_teams'].isoformat(),
                'signal_shepherds': {
                    area: time.isoformat()
                    for area, time in staging_times['signal_shepherds'].items()
                },
            },
        },
    })

    score_info = get_scores(comp.scores, match)
    if score_info:
        info['scores'] = score_info

    return info


@overload
def parse_difference_string(
    string: str,
    type_converter: Callable[[str], TParseable],
) -> Callable[[TParseable], bool]:
    ...


@overload
def parse_difference_string(
    string: str,
    type_converter: Callable[[str], int] = int,
) -> Callable[[int], bool]:
    ...


def parse_difference_string(
    string: str,
    type_converter: Callable[[str], TParseable] = int,  # type: ignore[assignment]
) -> Callable[[TParseable], bool]:
    """
    Parse a difference string (x..x, ..x, x.., x) and return a function that
    accepts a single argument and returns ``True`` if it is in the difference.
    """
    separator = '..'
    if string == separator:
        raise ValueError('Must specify at least one bound.')
    tokens = string.split(separator)

    if len(tokens) > 2:
        raise ValueError('Argument is not a different string.')
    elif len(tokens) == 1:
        converted_token = type_converter(tokens[0])
        return lambda x: x == converted_token
    elif len(tokens) == 2:
        if not tokens[1]:
            lower_bound = type_converter(tokens[0])
            return lambda x: x >= lower_bound
        elif not tokens[0]:
            upper_bound = type_converter(tokens[1])
            return lambda x: x <= upper_bound
        else:
            lhs = type_converter(tokens[0])
            rhs = type_converter(tokens[1])
            if lhs > rhs:
                raise ValueError('Bounds are the wrong way around.')
            return lambda x: lhs <= x <= rhs
    else:
        raise AssertionError('Argument contains unknown input.')
