"""JSON formatting routines."""

import datetime
from enum import Enum
from typing import Any

import simplejson
from flask import g
from werkzeug.http import http_date

from sr.comp.comp import SRComp
from sr.comp.http.query_utils import match_json_info
from sr.comp.match_period import Match


class JsonEncoder(simplejson.JSONEncoder):
    """A JSON encoder that deals with various types used in SRComp."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # The following is required because the default JSON encoder does
        # stuff with these types. We can put them back in manually ourselves
        # with the 'default' method if we require. It's a bit hacky, but it
        # works.
        # In an ideal world, the types we deal with in 'default' would have
        # appropriate '_asdict' methods.
        kwargs['namedtuple_as_object'] = False
        kwargs['tuple_as_array'] = False
        super().__init__(*args, **kwargs)

    def default(self, obj: object) -> Any:
        if isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, Match):
            comp: SRComp = g.comp_man.get_comp()
            return match_json_info(comp, obj)
        elif isinstance(obj, datetime.datetime):
            return http_date(obj.utctimetuple())
        elif isinstance(obj, datetime.date):
            return http_date(obj.timetuple())
        else:
            return super().default(obj)
