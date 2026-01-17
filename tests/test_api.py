from __future__ import annotations

import contextlib
import os.path
import unittest
from collections.abc import Iterable, Iterator, Mapping
from typing import Any

from flask.testing import FlaskClient
from freezegun import freeze_time

from sr.comp.http import app

FlaskTestResponse = tuple[Iterable[bytes], str, Mapping[str, str]]

COMPSTATE = os.path.join(os.path.dirname(__file__), 'dummy')
app.config['COMPSTATE'] = COMPSTATE

MATCH_0 = [
    {
        'num': 0,
        'display_name': 'Match 0',
        'arena': 'A',
        'type': 'league',
        'teams': [None, 'CLY', 'TTN', None],
        'scores': {
            'game': {'CLY': 9, 'TTN': 6},
            'league': {'CLY': 8, 'TTN': 6},
            'ranking': {'CLY': 1, 'TTN': 2},
        },
        'state': 'released',
        'times': {
            'slot': {
                'start': '2014-04-26T13:00:00+01:00',
                'end': '2014-04-26T13:05:00+01:00',
            },
            'game': {
                'start': '2014-04-26T13:01:30+01:00',
                'end': '2014-04-26T13:04:30+01:00',
            },
            'operations': {
                'release_threshold': '2014-04-26T13:01:30+01:00',
            },
            'staging': {
                'opens': '2014-04-26T12:56:30+01:00',
                'closes': '2014-04-26T12:59:30+01:00',
                'signal_teams': '2014-04-26T12:57:30+01:00',
                'signal_shepherds': {
                    'Blue': '2014-04-26T12:57:29+01:00',
                    'Green': '2014-04-26T12:58:29+01:00',
                },
            },
        },
    },
    {
        'num': 0,
        'display_name': 'Match 0',
        'arena': 'B',
        'type': 'league',
        'teams': ['GRS', 'QMC', None, None],
        'scores': {
            'game': {'QMC': 3, 'GRS': 5},
            'league': {'QMC': 6, 'GRS': 8},
            'ranking': {'QMC': 2, 'GRS': 1},
        },
        'state': 'released',
        'times': {
            'slot': {
                'start': '2014-04-26T13:00:00+01:00',
                'end': '2014-04-26T13:05:00+01:00',
            },
            'game': {
                'start': '2014-04-26T13:01:30+01:00',
                'end': '2014-04-26T13:04:30+01:00',
            },
            'operations': {
                'release_threshold': '2014-04-26T13:01:30+01:00',
            },
            'staging': {
                'opens': '2014-04-26T12:56:30+01:00',
                'closes': '2014-04-26T12:59:30+01:00',
                'signal_teams': '2014-04-26T12:57:30+01:00',
                'signal_shepherds': {
                    'Blue': '2014-04-26T12:57:29+01:00',
                    'Green': '2014-04-26T12:58:29+01:00',
                },
            },
        },
    },
]


class ApiError(Exception):
    def __init__(self, name: str, code: int) -> None:
        super().__init__(name, code)
        self.name = name
        self.code = code


class ApiTests(unittest.TestCase):
    maxDiff = 8000

    def server_get(self, endpoint: str) -> Any:
        response = self.client.get(endpoint)
        json_response = response.json
        code = int(response.status.split(' ')[0])

        assert json_response is not None, "No json data"  # placate mypy

        if 200 <= code <= 299:
            return json_response

        elif 400 <= code <= 499:
            self.assertEqual(code, json_response['error']['code'])
            error = json_response['error']
            raise ApiError(error['name'], error['code'])

        else:
            raise AssertionError()  # server error

    @contextlib.contextmanager
    def assertRaisesApiError(self, name: str, code: int) -> Iterator[None]:
        with self.assertRaises(ApiError) as cm:
            yield

        self.assertEqual(name, cm.exception.name)
        self.assertEqual(code, cm.exception.code)

    def setUp(self) -> None:
        super().setUp()
        self.client = FlaskClient(app)

    def test_endpoints(self) -> None:
        endpoints = [
            '/',
            '/arenas',
            '/arenas/A',
            '/arenas/B',
            '/teams',
            '/teams/CLF',
            '/corners',
            '/corners/0',
            '/corners/1',
            '/corners/2',
            '/corners/3',
            '/locations',
            '/locations/a-group',
            '/matches',
            '/matches?arena=A',
            '/matches?arena=B',
            '/matches?num=0..1',
            '/matches?arena=B&num=1',
            '/matches?type=knockout',
            '/matches?type=league&limit=10',
            '/matches/last_scored',
            '/periods',
            '/state',
        ]

        for e in endpoints:
            with self.subTest(e):
                self.server_get(e)

    def test_parent(self) -> None:
        response = self.client.get('')

        code_prefix = response.status[:4]
        self.assertIn(code_prefix, ('308 ', '301 '), "Should indicate a redirect")

        self.assertIn(
            'Location',
            response.headers,
            "Should have indicated where to redirect to",
        )

        self.assertEqual('http://localhost/', response.headers['Location'])

    def test_root(self) -> None:
        expected = {
            'config': '/config',
            'arenas': '/arenas',
            'teams': '/teams',
            'corners': '/corners',
            'locations': '/locations',
            'matches': '/matches',
            'periods': '/periods',
            'state': '/state',
            'current': '/current',
            'knockout': '/knockout',
        }
        self.assertEqual(expected, self.server_get('/'))

    def test_state(self) -> None:
        state_val = self.server_get('/state')['state']
        self.assertNotEqual('', state_val)

    def test_corner(self) -> None:
        self.assertEqual(
            {
                'get': '/corners/0',
                'number': 0,
                'colour': '#00ff00',
            },
            self.server_get('/corners/0'),
        )

    def test_invalid_corner(self) -> None:
        with self.assertRaisesApiError('NotFound', 404):
            self.server_get('/corners/12')

    def test_config(self) -> None:
        expected = {
            'pre': 90,
            'match': 180,
            'post': 30,
            'total': 300,
        }

        cfg = self.server_get('/config')['config']

        self.assertEqual(expected, cfg['match_slots'])

    def test_arena(self) -> None:
        self.assertEqual(self.server_get('/arenas/A'), {
            'get': '/arenas/A',
            'name': 'A',
            'colour': '#ff0000',
            'display_name': 'A',
        })

    def test_invalid_arena(self) -> None:
        with self.assertRaisesApiError('NotFound', 404):
            self.server_get('/arenas/Z')

    def test_arenas(self) -> None:
        expected = {
            'A': {
                'get': '/arenas/A',
                'name': 'A',
                'colour': '#ff0000',
                'display_name': 'A',
            },
            'B': {
                'get': '/arenas/B',
                'name': 'B',
                'display_name': 'B',
            },
        }
        self.assertEqual(expected, self.server_get('/arenas')['arenas'])

    def test_location(self) -> None:
        expected = {
            "description": "A group of some sort, it contains a number of teams.",
            "display_name": "A group",
            "get": "/locations/a-group",
            "shepherds": {
                "colour": "#A9A9F5",
                "name": "Blue",
            },
            "teams": ["BAY", "BDF", "BGS", "BPV", "BRK", "BRN", "BWS", "CCR",  # noqa: BWR001
                      "CGS", "CLF", "CLY", "CPR", "CRB", "DSF", "EMM", "GRD",
                      "GRS", "GYG", "HRS", "HSO", "HYP", "HZW", "ICE", "JMS",
                      "KDE", "KES", "KHS", "LFG"],
        }
        self.assertEqual(expected, self.server_get('/locations/a-group'))

    def test_invalid_location(self) -> None:
        with self.assertRaisesApiError('NotFound', 404):
            self.server_get('/locations/nope')

    def test_locations(self) -> None:
        a = {
            "description": "A group of some sort, it contains a number of teams.",
            "display_name": "A group",
            "get": "/locations/a-group",
            "shepherds": {
                "colour": "#A9A9F5",
                "name": "Blue",
            },
            "teams": ["BAY", "BDF", "BGS", "BPV", "BRK", "BRN", "BWS", "CCR",  # noqa: BWR001
                      "CGS", "CLF", "CLY", "CPR", "CRB", "DSF", "EMM", "GRD",
                      "GRS", "GYG", "HRS", "HSO", "HYP", "HZW", "ICE", "JMS",
                      "KDE", "KES", "KHS", "LFG"],
        }
        b = {
            "display_name": "Another group",
            "get": "/locations/b-group",
            "shepherds": {
                "colour": "green",
                "name": "Green",
            },
            "teams": ["LSS", "MAI", "MAI2", "MEA", "MFG", "NHS", "PAG", "PAS",  # noqa: BWR001
                      "PSC", "QEH", "QMC", "QMS", "RED", "RGS", "RUN", "RWD",
                      "SCC", "SEN", "SGS", "STA", "SWI", "TBG", "TTN", "TWG",
                      "WYC"],
        }

        self.assertEqual(
            {'a-group': a, 'b-group': b},
            self.server_get('/locations')['locations'],
        )

    def test_team(self) -> None:
        expected = {
            'tla': 'CLF',
            'name': 'Clifton High School',
            'league_pos': 36,
            'location': {
                'get': '/locations/a-group',
                'name': 'a-group',
            },
            'rookie': False,
            'scores': {
                'league': 68,
                'game': 69,
            },
            'get': '/teams/CLF',
        }
        self.assertEqual(expected, self.server_get('/teams/CLF'))

    def test_team_image(self) -> None:
        self.assertEqual(
            '/teams/BAY/image',
            self.server_get('/teams/BAY')['image_url'],
        )

    def test_no_team_image(self) -> None:
        with self.assertRaisesApiError('NotFound', 404):
            self.server_get('/teams/BEES/image')

    def test_bad_team(self) -> None:
        with self.assertRaisesApiError('NotFound', 404):
            self.server_get('/teams/BEES')

    def test_matches(self) -> None:
        expected = {
            'matches': [
                {
                    'num': 0,
                    'display_name': 'Match 0',
                    'arena': 'A',
                    'type': 'league',
                    'teams': [None, 'CLY', 'TTN', None],
                    'scores': {
                        'game': {'CLY': 9, 'TTN': 6},
                        'league': {'CLY': 8, 'TTN': 6},
                        'ranking': {'CLY': 1, 'TTN': 2},
                    },
                    'state': 'released',
                    'times': {
                        'slot': {
                            'start': '2014-04-26T13:00:00+01:00',
                            'end': '2014-04-26T13:05:00+01:00',
                        },
                        'game': {
                            'start': '2014-04-26T13:01:30+01:00',
                            'end': '2014-04-26T13:04:30+01:00',
                        },
                        'operations': {
                            'release_threshold': '2014-04-26T13:01:30+01:00',
                        },
                        'staging': {
                            'opens': '2014-04-26T12:56:30+01:00',
                            'closes': '2014-04-26T12:59:30+01:00',
                            'signal_teams': '2014-04-26T12:57:30+01:00',
                            'signal_shepherds': {
                                'Blue': '2014-04-26T12:57:29+01:00',
                                'Green': '2014-04-26T12:58:29+01:00',
                            },
                        },
                    },
                },
            ],
            'last_scored': 99,
        }
        self.assertEqual(
            expected,
            self.server_get('/matches?num=0&arena=A'),
        )

    def test_match_forwards_limit(self) -> None:
        expected = {
            'matches': [
                {
                    'num': 0,
                    'display_name': 'Match 0',
                    'arena': 'A',
                    'type': 'league',
                    'teams': [None, 'CLY', 'TTN', None],
                    'scores': {
                        'game': {'CLY': 9, 'TTN': 6},
                        'league': {'CLY': 8, 'TTN': 6},
                        'ranking': {'CLY': 1, 'TTN': 2},
                    },
                    'state': 'released',
                    'times': {
                        'slot': {
                            'start': '2014-04-26T13:00:00+01:00',
                            'end': '2014-04-26T13:05:00+01:00',
                        },
                        'game': {
                            'start': '2014-04-26T13:01:30+01:00',
                            'end': '2014-04-26T13:04:30+01:00',
                        },
                        'operations': {
                            'release_threshold': '2014-04-26T13:01:30+01:00',
                        },
                        'staging': {
                            'opens': '2014-04-26T12:56:30+01:00',
                            'closes': '2014-04-26T12:59:30+01:00',
                            'signal_teams': '2014-04-26T12:57:30+01:00',
                            'signal_shepherds': {
                                'Blue': '2014-04-26T12:57:29+01:00',
                                'Green': '2014-04-26T12:58:29+01:00',
                            },
                        },
                    },
                },
            ],
            'last_scored': 99,
        }
        self.assertEqual(
            expected,
            self.server_get('/matches?arena=A&limit=1'),
        )

    def test_match_backwards_limit(self) -> None:
        expected = {
            'matches': [
                {
                    'display_name': 'Final (#129)',
                    'type': 'knockout',
                    'num': 129,
                    'arena': 'A',
                    'state': 'released',
                    'times': {
                        'game': {
                            'end': '2014-04-27T17:29:30+01:00',
                            'start': '2014-04-27T17:26:30+01:00',
                        },
                        'slot': {
                            'end': '2014-04-27T17:30:00+01:00',
                            'start': '2014-04-27T17:25:00+01:00',
                        },
                        'operations': {
                            'release_threshold': '2014-04-27T17:26:30+01:00',
                        },
                        'staging': {
                            'opens': '2014-04-27T17:21:30+01:00',
                            'closes': '2014-04-27T17:24:30+01:00',
                            'signal_teams': '2014-04-27T17:22:30+01:00',
                            'signal_shepherds': {
                                'Blue': '2014-04-27T17:22:29+01:00',
                                'Green': '2014-04-27T17:23:29+01:00',
                            },
                        },
                    },
                    'teams': ['???', '???', '???', '???'],
                },
            ],
            'last_scored': 99,
        }
        self.assertEqual(
            expected,
            self.server_get('/matches?arena=A&limit=-1'),
        )

    def test_match_filter_naive_datetime(self) -> None:
        expected = {
            'matches': [
                {
                    'display_name': 'Final (#129)',
                    'type': 'knockout',
                    'num': 129,
                    'arena': 'A',
                    'state': 'released',
                    'times': {
                        'game': {
                            'end': '2014-04-27T17:29:30+01:00',
                            'start': '2014-04-27T17:26:30+01:00',
                        },
                        'slot': {
                            'end': '2014-04-27T17:30:00+01:00',
                            'start': '2014-04-27T17:25:00+01:00',
                        },
                        'operations': {
                            'release_threshold': '2014-04-27T17:26:30+01:00',
                        },
                        'staging': {
                            'opens': '2014-04-27T17:21:30+01:00',
                            'closes': '2014-04-27T17:24:30+01:00',
                            'signal_teams': '2014-04-27T17:22:30+01:00',
                            'signal_shepherds': {
                                'Blue': '2014-04-27T17:22:29+01:00',
                                'Green': '2014-04-27T17:23:29+01:00',
                            },
                        },
                    },
                    'teams': ['???', '???', '???', '???'],
                },
            ],
            'last_scored': 99,
        }
        self.assertEqual(
            expected,
            self.server_get('/matches?arena=A&limit=-1'),
        )

    def test_invalid_match_filter(self) -> None:
        with self.assertRaisesApiError('UnknownMatchFilter', 400):
            self.server_get('/matches?number=0&arena=A')

    def test_invalid_match_filter_value(self) -> None:
        with self.assertRaisesApiError('BadRequest', 400):
            self.server_get('/matches?num=&arena=A')

    def test_match_filter_time(self) -> None:
        expected = {
            'matches': [
                {
                    'display_name': 'Final (#129)',
                    'type': 'knockout',
                    'num': 129,
                    'arena': 'A',
                    'state': 'released',
                    'times': {
                        'game': {
                            'end': '2014-04-27T17:29:30+01:00',
                            'start': '2014-04-27T17:26:30+01:00',
                        },
                        'slot': {
                            'end': '2014-04-27T17:30:00+01:00',
                            'start': '2014-04-27T17:25:00+01:00',
                        },
                        'operations': {
                            'release_threshold': '2014-04-27T17:26:30+01:00',
                        },
                        'staging': {
                            'opens': '2014-04-27T17:21:30+01:00',
                            'closes': '2014-04-27T17:24:30+01:00',
                            'signal_teams': '2014-04-27T17:22:30+01:00',
                            'signal_shepherds': {
                                'Blue': '2014-04-27T17:22:29+01:00',
                                'Green': '2014-04-27T17:23:29+01:00',
                            },
                        },
                    },
                    'teams': ['???', '???', '???', '???'],
                },
            ],
            'last_scored': 99,
        }
        self.assertEqual(
            expected,
            self.server_get('/matches?game_start_time=2014-04-27T17:26:30%2B01:00'),
        )

    def test_invalid_match_filter_spacey_time(self) -> None:
        with self.assertRaisesApiError('BadRequest', 400):
            self.server_get('/matches?game_start_time=2014-04-27T17:26:30+01:00')

    def test_invalid_match_filter_naive_time(self) -> None:
        with self.assertRaisesApiError('BadRequest', 400):
            self.server_get('/matches?game_start_time=2014-04-27T17:26:30')

    def test_invalid_match_filter_naive_time_range(self) -> None:
        with self.assertRaisesApiError('BadRequest', 400):
            self.server_get('/matches?game_start_time=2014-04-27T17:26:30..')

    def test_last_scored(self) -> None:
        self.assertEqual(
            {'last_scored': 99},
            self.server_get('/matches/last_scored'),
        )

    def test_invalid_match_type(self) -> None:
        with self.assertRaisesApiError('BadRequest', 400):
            self.server_get('/matches?type=bees')

    def test_periods(self) -> None:
        expected = {"periods": [
            {
                "type": "league",
                "description": "Saturday, 26 April 2014, afternoon",
                "end_time": "Sat, 26 Apr 2014 16:30:00 GMT",
                "matches": {
                    "first_num": 0,
                    "last_num": 52,
                },
                "max_end_time": "Sat, 26 Apr 2014 16:40:00 GMT",
                "start_time": "Sat, 26 Apr 2014 12:00:00 GMT",
            },
            {
                "type": "league",
                "description": "Sunday, 27 April 2014, morning",
                "end_time": "Sun, 27 Apr 2014 11:15:00 GMT",
                "matches": {
                    "first_num": 53,
                    "last_num": 86,
                },
                "max_end_time": "Sun, 27 Apr 2014 11:20:00 GMT",
                "start_time": "Sun, 27 Apr 2014 08:30:00 GMT",
            },
            {
                "type": "league",
                "description": "Sunday, 27 April 2014, afternoon",
                "end_time": "Sun, 27 Apr 2014 14:10:00 GMT",
                "matches": {
                    "first_num": 87,
                    "last_num": 110,
                },
                "max_end_time": "Sun, 27 Apr 2014 14:10:00 GMT",
                "start_time": "Sun, 27 Apr 2014 12:15:00 GMT",
            },
            {
                "type": "knockout",
                "description": "The Knockouts, Sunday, 27 April 2014, afternoon",
                "end_time": "Sun, 27 Apr 2014 16:30:00 GMT",
                "matches": {
                    "first_num": 111,
                    "last_num": 129,
                },
                "max_end_time": "Sun, 27 Apr 2014 16:30:00 GMT",
                "start_time": "Sun, 27 Apr 2014 14:30:00 GMT",
            },
        ]}

        self.assertEqual(expected, self.server_get('/periods'))

    @freeze_time('2014-04-26 12:01:00')  # UTC
    def test_current_time(self) -> None:
        self.assertEqual(
            '2014-04-26T13:01:00+01:00',
            self.server_get('/current')['time'],
        )

    @freeze_time('2014-04-26 12:30:00')  # UTC
    def test_current_delay(self) -> None:
        self.assertEqual(
            15,
            self.server_get('/current')['delay'],
        )

    @freeze_time('2014-04-26 11:55:00')  # UTC
    def test_current_shepherding_match_none(self) -> None:
        match_list = self.server_get('/current')['shepherding_matches']

        match_list.sort(key=lambda match: match['arena'])

        self.assertEqual([], match_list)

    @freeze_time('2014-04-26 11:58:00')  # UTC
    def test_current_shepherding_match(self) -> None:
        match_list = self.server_get('/current')['shepherding_matches']

        match_list.sort(key=lambda match: match['arena'])

        self.assertEqual(MATCH_0, match_list)

    @freeze_time('2014-04-26 11:55:00')  # UTC
    def test_current_staging_match_none(self) -> None:
        match_list = self.server_get('/current')['staging_matches']

        match_list.sort(key=lambda match: match['arena'])

        self.assertEqual([], match_list)

    @freeze_time('2014-04-26 11:57:00')  # UTC
    def test_current_staging_match(self) -> None:
        match_list = self.server_get('/current')['staging_matches']

        match_list.sort(key=lambda match: match['arena'])

        self.assertEqual(MATCH_0, match_list)

    @freeze_time('2014-04-26 12:01:00')  # UTC
    def test_current_match(self) -> None:
        match_list = self.server_get('/current')['matches']

        match_list.sort(key=lambda match: match['arena'])

        self.assertEqual(MATCH_0, match_list)

    def test_knockouts(self) -> None:
        ref = [
            [
                {
                    'arena': 'A',
                    'num': 111,
                    'display_name': 'Match 111',
                    'teams': ['???', '???', '???', '???'],
                    'state': 'released',
                    'times': None,
                    'type': 'knockout',
                },
                {
                    'arena': 'B',
                    'num': 111,
                    'display_name': 'Match 111',
                    'teams': [None, '???', '???', '???'],
                    'state': 'released',
                    'times': None,
                    'type': 'knockout',
                },
                {
                    'arena': 'A',
                    'num': 112,
                    'display_name': 'Match 112',
                    'teams': ['???', '???', '???', '???'],
                    'state': 'released',
                    'times': None,
                    'type': 'knockout',
                },
                {
                    'arena': 'B',
                    'num': 112,
                    'display_name': 'Match 112',
                    'teams': ['???', '???', '???', None],
                    'state': 'released',
                    'times': None,
                    'type': 'knockout',
                },
                {
                    'arena': 'A',
                    'num': 113,
                    'display_name': 'Match 113',
                    'teams': ['???', '???', '???', '???'],
                    'state': 'released',
                    'times': None,
                    'type': 'knockout',
                },
                {
                    'arena': 'B',
                    'num': 113,
                    'display_name': 'Match 113',
                    'teams': ['???', '???', '???', None],
                    'state': 'released',
                    'times': None,
                    'type': 'knockout',
                },
                {
                    'arena': 'A',
                    'num': 114,
                    'display_name': 'Match 114',
                    'teams': ['???', '???', None, '???'],
                    'state': 'released',
                    'times': None,
                    'type': 'knockout',
                },
                {
                    'arena': 'B',
                    'num': 114,
                    'display_name': 'Match 114',
                    'teams': ['???', None, '???', '???'],
                    'state': 'released',
                    'times': None,
                    'type': 'knockout',
                },
                {
                    'arena': 'A',
                    'num': 115,
                    'display_name': 'Match 115',
                    'teams': ['???', None, '???', '???'],
                    'state': 'released',
                    'times': None,
                    'type': 'knockout',
                },
                {
                    'arena': 'B',
                    'num': 115,
                    'display_name': 'Match 115',
                    'teams': [None, '???', '???', '???'],
                    'state': 'released',
                    'times': None,
                    'type': 'knockout',
                },
                {
                    'arena': 'A',
                    'num': 116,
                    'display_name': 'Match 116',
                    'teams': [None, '???', '???', '???'],
                    'state': 'released',
                    'times': None,
                    'type': 'knockout',
                },
                {
                    'arena': 'B',
                    'num': 116,
                    'display_name': 'Match 116',
                    'teams': ['???', '???', '???', '???'],
                    'state': 'released',
                    'times': None,
                    'type': 'knockout',
                },
                {
                    'arena': 'A',
                    'num': 117,
                    'display_name': 'Match 117',
                    'teams': [None, '???', '???', '???'],
                    'state': 'released',
                    'times': None,
                    'type': 'knockout',
                },
                {
                    'arena': 'B',
                    'num': 117,
                    'display_name': 'Match 117',
                    'teams': ['???', '???', '???', None],
                    'state': 'released',
                    'times': None,
                    'type': 'knockout',
                },
                {
                    'arena': 'A',
                    'num': 118,
                    'display_name': 'Match 118',
                    'teams': [None, '???', '???', '???'],
                    'state': 'released',
                    'times': None,
                    'type': 'knockout',
                },
                {
                    'arena': 'B',
                    'num': 118,
                    'display_name': 'Match 118',
                    'teams': ['???', '???', '???', '???'],
                    'state': 'released',
                    'times': None,
                    'type': 'knockout',
                },
            ],
            [
                {
                    'arena': 'A',
                    'num': 119,
                    'display_name': 'Match 119',
                    'teams': ['???', '???', '???', '???'],
                    'state': 'released',
                    'times': None,
                    'type': 'knockout',
                },
                {
                    'arena': 'B',
                    'num': 119,
                    'display_name': 'Match 119',
                    'teams': ['???', '???', '???', '???'],
                    'state': 'released',
                    'times': None,
                    'type': 'knockout',
                },
                {
                    'arena': 'A',
                    'num': 120,
                    'display_name': 'Match 120',
                    'teams': ['???', '???', '???', '???'],
                    'state': 'released',
                    'times': None,
                    'type': 'knockout',
                },
                {
                    'arena': 'B',
                    'num': 120,
                    'display_name': 'Match 120',
                    'teams': ['???', '???', '???', '???'],
                    'state': 'released',
                    'times': None,
                    'type': 'knockout',
                },
                {
                    'arena': 'A',
                    'num': 121,
                    'display_name': 'Match 121',
                    'teams': ['???', '???', '???', '???'],
                    'state': 'released',
                    'times': None,
                    'type': 'knockout',
                },
                {
                    'arena': 'B',
                    'num': 121,
                    'display_name': 'Match 121',
                    'teams': ['???', '???', '???', '???'],
                    'state': 'released',
                    'times': None,
                    'type': 'knockout',
                },
                {
                    'arena': 'A',
                    'num': 122,
                    'display_name': 'Match 122',
                    'teams': ['???', '???', '???', '???'],
                    'state': 'released',
                    'times': None,
                    'type': 'knockout',
                },
                {
                    'arena': 'B',
                    'num': 122,
                    'display_name': 'Match 122',
                    'teams': ['???', '???', '???', '???'],
                    'state': 'released',
                    'times': None,
                    'type': 'knockout',
                },
            ],
            [
                {
                    'arena': 'A',
                    'num': 123,
                    'display_name': 'Quarter 1 (#123)',
                    'teams': ['???', '???', '???', '???'],
                    'state': 'released',
                    'times': None,
                    'type': 'knockout',
                },
                {
                    'arena': 'A',
                    'num': 124,
                    'display_name': 'Quarter 2 (#124)',
                    'teams': ['???', '???', '???', '???'],
                    'state': 'released',
                    'times': None,
                    'type': 'knockout',
                },
                {
                    'arena': 'A',
                    'num': 125,
                    'display_name': 'Quarter 3 (#125)',
                    'teams': ['???', '???', '???', '???'],
                    'state': 'released',
                    'times': None,
                    'type': 'knockout',
                },
                {
                    'arena': 'A',
                    'num': 126,
                    'display_name': 'Quarter 4 (#126)',
                    'teams': ['???', '???', '???', '???'],
                    'state': 'released',
                    'times': None,
                    'type': 'knockout',
                },
            ],
            [
                {
                    'arena': 'A',
                    'num': 127,
                    'display_name': 'Semi 1 (#127)',
                    'teams': ['???', '???', '???', '???'],
                    'state': 'released',
                    'times': None,
                    'type': 'knockout',
                },
                {
                    'arena': 'A',
                    'num': 128,
                    'display_name': 'Semi 2 (#128)',
                    'teams': ['???', '???', '???', '???'],
                    'state': 'released',
                    'times': None,
                    'type': 'knockout',
                },
            ],
            [
                {
                    'arena': 'A',
                    'num': 129,
                    'display_name': 'Final (#129)',
                    'teams': ['???', '???', '???', '???'],
                    'state': 'released',
                    'times': None,
                    'type': 'knockout',
                },
            ],
        ]
        actual_rounds = self.server_get('knockout')['rounds']

        times_keys = ['game', 'operations', 'slot', 'staging']
        for r in actual_rounds:
            for m in r:
                with self.subTest(match=m):
                    self.assertIn('times', m)
                    keys = sorted(m['times'].keys())
                    self.assertEqual(times_keys, keys, "Wrong time keys in")
                m['times'] = None

        # Our own assertion since the built-in ones don't cope with such a
        # large structure very well (ie, the failure output sucks)
        for r_num, matches in enumerate(ref):
            with self.subTest(round=r_num):
                self.assertLess(
                    r_num,
                    len(actual_rounds),
                    "Failed to get round from server",
                )

                actual_matches = actual_rounds[r_num]

                for m_num, match in enumerate(matches):
                    with self.subTest(round=r_num, match=m_num):
                        self.assertLess(
                            m_num,
                            len(actual_matches),
                            "Failed to get match from server",
                        )

                        actual_match = actual_matches[m_num]

                        self.assertEqual(match, actual_match)

        # Just in case the above is faulty
        self.assertEqual(ref, actual_rounds)

    def test_tiebreaker(self) -> None:
        with self.assertRaisesApiError('NotFound', 404):
            self.server_get('/tiebreaker')
