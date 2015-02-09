from __future__ import print_function

import json
import os.path
from flask.testing import FlaskClient

from nose.tools import eq_

from sr.comp.http import app

COMPSTATE = os.path.join(os.path.dirname(__file__), 'dummy')
app.config['COMPSTATE'] = COMPSTATE

CLIENT = FlaskClient(app)

class APIError(Exception):
    pass

def server_get(endpoint):
    response, code, header = CLIENT.get(endpoint)
    response_code = int(code.split(' ')[0])
    response_data = b''.join(response)
    if response_code != 200:
        raise APIError('Returned status {}'.format(response_code))
    return json.loads(response_data.decode('utf-8'))

def test_endpoints():
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
        '/matches',
        '/matches?arenas=A&range=current',
        '/matches?arenas=B&range=current',
        '/matches?range=0-1',
        '/matches?arenas=B&range=1',
        '/matches?type=knockout',
        '/state'
    ]

    for e in endpoints:
        yield server_get, e

def test_root():
    eq_(server_get('/'), {'config': '/config',
                          'arenas': '/arenas',
                          'teams': '/teams',
                          'corners': '/corners',
                          'matches': '/matches',
                          'state': '/state'})

def test_state():
    assert isinstance(server_get('/state')['state'], str)

def test_corner():
    eq_(server_get('/corners/0'), {'get': '/corners/0',
                                   'number': 0,
                                   'colour': '#00ff00'})

def test_config():
    eq_(server_get('/config'), {'config':
                                 {'match_periods':
                                   {'pre': 90,
                                    'match': 180,
                                    'post': 30,
                                    'total': 300}}})

def test_arena():
    eq_(server_get('/arenas/A'), {'get': '/arenas/A',
                                  'name': 'A',
                                  'display_name': 'A'})

def test_arenas():
    eq_(server_get('/arenas')['arenas'],
          {'A': {'get': '/arenas/A',
                 'name': 'A',
                 'display_name': 'A'},
           'B': {'get': '/arenas/B',
                 'name': 'B',
                 'display_name': 'B'}})
