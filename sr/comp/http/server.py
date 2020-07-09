import datetime
import os.path
from typing import Any, Dict, List, Mapping, Tuple, Union

import dateutil.parser
import dateutil.tz
import werkzeug.exceptions
from flask import abort, Flask, g, jsonify, request, send_file, url_for
from flask.wrappers import Response
from pkg_resources import Distribution, working_set

from sr.comp.arenas import Arena, Corner, CornerNumber
from sr.comp.comp import SRComp
from sr.comp.http import errors
from sr.comp.http.json_encoder import JsonEncoder
from sr.comp.http.manager import SRCompManager
from sr.comp.http.query_utils import match_json_info, parse_difference_string
from sr.comp.match_period import MatchPeriod, MatchType
from sr.comp.teams import Team
from sr.comp.types import ArenaName, MatchNumber, Region, RegionName, TLA

from .query_utils import MatchInfo

app = Flask('sr.comp.http')
app.json_encoder = JsonEncoder

comp_man = SRCompManager()


@app.before_request
def before_request() -> None:
    if "COMPSTATE" in app.config:
        comp_man.root_dir = os.path.realpath(app.config["COMPSTATE"])
    g.comp_man = comp_man


@app.after_request
def after_request(resp: Response) -> Response:
    if 'Origin' in request.headers:
        resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


@app.route('/')
def root() -> str:
    return jsonify(
        arenas=url_for('arenas'),
        teams=url_for('teams'),
        corners=url_for('corners'),
        config=url_for('config'),
        state=url_for('state'),
        locations=url_for('locations'),
        matches=url_for('matches'),
        periods=url_for('match_periods'),
        current=url_for('current_state'),
        knockout=url_for('knockout'),
    )


def format_arena(arena: Arena) -> Dict[str, Any]:
    data = {'get': url_for('get_arena', name=arena.name)}
    data.update(arena._asdict())
    if not arena.colour:
        del data['colour']
    return data


@app.route('/arenas')
def arenas() -> str:
    comp = g.comp_man.get_comp()  # type: SRComp
    return jsonify(arenas={
        name: format_arena(arena)
        for name, arena in comp.arenas.items()
    })


@app.route('/arenas/<name>')
def get_arena(name: str) -> str:
    comp = g.comp_man.get_comp()  # type: SRComp

    if name not in comp.arenas:
        abort(404)

    arena_name = ArenaName(name)

    return jsonify(**format_arena(comp.arenas[arena_name]))


def format_location(location: Region) -> Dict[str, Any]:
    data = {
        'get': url_for('get_location', name=location['name']),
        **location,
    }  # type: Dict[str, Any]
    del data['name']
    return data


@app.route('/locations')
def locations() -> str:
    comp = g.comp_man.get_comp()  # type: SRComp

    return jsonify(locations={
        name: format_location(location)
        for name, location in comp.venue.locations.items()
    })


@app.route('/locations/<name>')
def get_location(name: str) -> str:
    comp = g.comp_man.get_comp()  # type: SRComp

    try:
        location = comp.venue.locations[RegionName(name)]
    except KeyError:
        abort(404)

    return jsonify(format_location(location))


def team_info(comp: SRComp, team: Team) -> Dict[str, Any]:
    scores = comp.scores.league.teams[team.tla]
    league_pos = comp.scores.league.positions[team.tla]
    location = comp.venue.get_team_location(team.tla)
    info = {
        'name': team.name,
        'get': url_for('get_team', tla=team.tla),
        'tla': team.tla,
        'league_pos': league_pos,
        'location': {
            'name': location,
            'get': url_for('get_location', name=location),
        },
        'scores': {
            'league': scores.league_points,
            'game': scores.game_points,
        },
    }

    if os.path.exists(os.path.join(
        g.comp_man.root_dir,
        'teams',
        'images',
        '{}.png'.format(team.tla),
    )):
        info['image_url'] = url_for('get_team_image', tla=team.tla)

    return info


@app.route('/teams')
def teams() -> str:
    comp = g.comp_man.get_comp()  # type: SRComp

    resp = {}
    for team in comp.teams.values():
        resp[team.tla] = team_info(comp, team)

    return jsonify(teams=resp)


@app.route('/teams/<tla>')
def get_team(tla: str) -> str:
    comp = g.comp_man.get_comp()  # type: SRComp

    try:
        team = comp.teams[TLA(tla)]
    except KeyError:
        abort(404)
    return jsonify(team_info(comp, team))


@app.route('/teams/<tla>/image')
def get_team_image(tla: str) -> Response:
    comp = g.comp_man.get_comp()  # type: SRComp

    try:
        team = comp.teams[TLA(tla)]
    except KeyError:
        abort(404)

    filename = os.path.join(
        g.comp_man.root_dir,
        'teams',
        'images',
        '{}.png'.format(team.tla),
    )
    if os.path.exists(filename):
        return send_file(filename, mimetype='image/png')
    else:
        abort(404)


def format_corner(corner: Corner) -> Dict[str, Any]:
    data = {'get': url_for('get_corner', number=corner.number)}
    data.update(corner._asdict())
    return data


@app.route("/corners")
def corners() -> str:
    comp = g.comp_man.get_comp()  # type: SRComp
    return jsonify(corners={
        number: format_corner(corner)
        for number, corner in comp.corners.items()
    })


@app.route("/corners/<int:number>")
def get_corner(number: int) -> str:
    comp = g.comp_man.get_comp()  # type: SRComp

    if number not in comp.corners:
        abort(404)

    corner_number = CornerNumber(number)

    return jsonify(**format_corner(comp.corners[corner_number]))


@app.route("/state")
def state() -> str:
    comp = g.comp_man.get_comp()  # type: SRComp
    return jsonify(state=comp.state)


def get_config_dict(comp: SRComp) -> Dict[str, Any]:
    LIBRARIES = ('sr.comp', 'sr.comp.http', 'sr.comp.ranker', 'league_ranker', 'flask')

    working_set_by_key = (
        # WorkingSet.by_key is not declared in the typeshed
        working_set.by_key   # type: ignore[attr-defined]
    )  # type: Mapping[str, Distribution]

    return {
        'match_slots': {
            k: int(v.total_seconds())
            for k, v in comp.schedule.match_slot_lengths.items()
        },
        'server': {
            library: working_set_by_key[library].version
            for library in LIBRARIES
            if library in working_set_by_key
        },
        'ping_period': 10,
    }


@app.route("/config")
def config() -> str:
    comp = g.comp_man.get_comp()  # type: SRComp
    return jsonify(config=get_config_dict(comp))


@app.route("/matches/last_scored")
def last_scored_match() -> str:
    comp = g.comp_man.get_comp()  # type: SRComp
    return jsonify(last_scored=comp.scores.last_scored_match)


@app.route("/matches")
def matches() -> str:
    comp = g.comp_man.get_comp()  # type: SRComp
    matches = []  # type: List[MatchInfo]
    for slots in comp.schedule.matches:
        matches.extend(
            match_json_info(comp, match)
            for match in slots.values()
        )

    def parse_date(string: str) -> datetime.datetime:
        if ' ' in string:
            raise errors.BadRequest(
                'Date string should not contain spaces. '
                "Did you pass in a '+'?",
            )
        else:
            return dateutil.parser.parse(string)

    filters = [
        ('type', MatchType, lambda x: x['type']),
        ('arena', str, lambda x: x['arena']),
        ('num', int, lambda x: x['num']),
        ('game_start_time', parse_date, lambda x: x['times']['game']['start']),
        ('game_end_time', parse_date, lambda x: x['times']['game']['end']),
        ('slot_start_time', parse_date, lambda x: x['times']['slot']['start']),
        ('slot_end_time', parse_date, lambda x: x['times']['slot']['end']),
    ]  # type: Any # TODO: re-work this to get checking

    # check for unknown filters
    filter_names = [name for name, _, _ in filters] + ['limit']
    for arg in request.args:
        if arg not in filter_names:
            raise errors.UnknownMatchFilter(arg)

    # actually run the filters
    for filter_key, filter_type, filter_value in filters:
        if filter_key in request.args:
            value = request.args[filter_key]
            try:
                predicate = parse_difference_string(value, filter_type)
                matches = [
                    match
                    for match in matches
                    if predicate(filter_type(filter_value(match)))  # type: ignore[no-untyped-call]  # noqa:E501
                ]
            except ValueError:
                raise errors.BadRequest("Bad value '{0}' for '{1}'.".format(value, filter_key))

    # limit the results
    try:
        limit = int(request.args['limit'])
    except KeyError:
        pass
    except ValueError:
        raise errors.BadRequest('Limit must be a positive or negative integer.')
    else:
        if limit == 0:
            matches = []
        elif limit > 0:
            matches = matches[:limit]
        elif limit < 0:
            matches = matches[limit:]
        else:
            raise AssertionError("Limit isn't a number?")

    return jsonify(matches=matches, last_scored=comp.scores.last_scored_match)


@app.route("/periods")
def match_periods() -> str:
    comp = g.comp_man.get_comp()  # type: SRComp

    def match_num(period: MatchPeriod, index: int) -> MatchNumber:
        games = list(period.matches[index].values())
        return games[0].num

    periods = []
    for match_period in comp.schedule.match_periods:
        data = match_period._asdict()
        data.pop('matches')
        if match_period.matches:
            data['matches'] = {
                'first_num': match_num(match_period, 0),
                'last_num': match_num(match_period, -1),
            }
        periods.append(data)

    return jsonify(periods=periods)


@app.route("/current")
def current_state() -> str:
    comp = g.comp_man.get_comp()  # type: SRComp

    time = datetime.datetime.now(comp.timezone)

    delay = comp.schedule.delay_at(time)
    delay_seconds = int(delay.total_seconds())

    matches = [
        match_json_info(comp, x)
        for x in comp.schedule.matches_at(time)
    ]

    staging_matches = []
    shepherding_matches = []
    for slot in comp.schedule.matches:
        for match in slot.values():
            staging_times = comp.schedule.get_staging_times(match)

            if time > staging_times['closes']:
                # Already done staging
                continue

            if staging_times['opens'] <= time:
                staging_matches.append(match_json_info(comp, match))

            first_signal = min(staging_times['signal_shepherds'].values())
            if first_signal <= time:
                shepherding_matches.append(match_json_info(comp, match))

    return jsonify(
        delay=delay_seconds,
        time=time.isoformat(),
        matches=matches,
        staging_matches=staging_matches,
        shepherding_matches=shepherding_matches,
    )


@app.route('/knockout')
def knockout() -> str:
    comp = g.comp_man.get_comp()  # type: SRComp
    return jsonify(rounds=comp.schedule.knockout_rounds)


@app.route('/tiebreaker')
def tiebreaker() -> str:
    comp = g.comp_man.get_comp()  # type: SRComp
    try:
        return jsonify(tiebreaker=comp.schedule.tiebreaker)
    except AttributeError:
        abort(404)


@app.errorhandler(werkzeug.exceptions.HTTPException)
def error_handler(
    e: werkzeug.exceptions.HTTPException,
) -> Union[
    werkzeug.exceptions.HTTPException,
    Tuple[str, int],
]:
    if e.code is None or e.code < 400:
        return e

    # fill up the error object with a name, description, code and details
    error = {
        'name': type(e).__name__,
        'description': e.description,
        'code': e.code,
    }

    # not all errors will have details
    try:
        error['details'] = e.details  # type: ignore[attr-defined]
    except AttributeError:
        pass

    return jsonify(error=error), e.code
