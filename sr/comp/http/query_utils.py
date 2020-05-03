"""Various utils for working with HTTP."""

import datetime
from typing import (
    Callable,
    Dict,
    List,
    Mapping,
    Optional,
    overload,
    Tuple,
    TypeVar,
    Union,
)
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

LeagueMatchScore = TypedDict('LeagueMatchScore', {
    'game': Mapping[TLA, GamePoints],
    'normalised': Dict[TLA, LeaguePoints],
    'ranking': Dict[TLA, RankedPosition],
})
KnockoutMatchScore = TypedDict('KnockoutMatchScore', {
    'game': Mapping[TLA, GamePoints],
    'league': Dict[TLA, LeaguePoints],
    'ranking': Dict[TLA, RankedPosition],
})
MatchScore = Union[LeagueMatchScore, KnockoutMatchScore]

Times = TypedDict('Times', {
    'start': str,
    'end': str,
})
StagingTimes = TypedDict('StagingTimes', {
    'opens': str,
    'closes': str,
    'signal_teams': str,
    'signal_shepherds': Dict[ShepherdName, str],
})
MatchTimings = TypedDict('MatchTimings', {
    'slot': Times,
    'game': Times,
    'staging': StagingTimes,
})
MatchInfo = TypedDict('MatchInfo', {
    'num': MatchNumber,
    'display_name': str,
    'arena': ArenaName,
    'teams': List[Optional[TLA]],
    'type': str,
    'times': MatchTimings,
})
ScoredMatchInfo = TypedDict('ScoredMatchInfo', {
    'num': MatchNumber,
    'display_name': str,
    'arena': ArenaName,
    'teams': List[Optional[TLA]],
    'type': str,
    'times': MatchTimings,
    'scores': MatchScore,
})

TParseable = TypeVar('TParseable', int, str, datetime.datetime)


def get_scores(scores: Scores, match: Match) -> Optional[MatchScore]:
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
        Tuple[BaseScores, Callable[[MatchId], Dict[TLA, RankedPosition]]],
        Tuple[None, None],
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


def match_json_info(comp: SRComp, match: Match) -> Union[MatchInfo, ScoredMatchInfo]:
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
        # TODO: once we're on Python 3.6+ we should be able to move to
        # class-based TypedDicts and thus make use of the totality flag, rather
        # than do this duplication.
        return ScoredMatchInfo({
            'scores': score_info,
            'num': info['num'],
            'display_name': info['display_name'],
            'arena': info['arena'],
            'teams': info['teams'],
            'type': info['type'],
            'times': info['times'],
        })

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
