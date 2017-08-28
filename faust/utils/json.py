"""JSON utilities."""
import datetime
import uuid
from decimal import Decimal
from typing import Any, List, Optional, Tuple, Type

DEFAULT_TEXTUAL_TYPES: List[Type] = [Decimal, uuid.UUID]

try:  # pragma: no cover
    from django.utils.functional import Promise
    DJANGO_TEXTUAL_TYPES = [Promise]
except ImportError:  # pragma: no cover
    DJANGO_TEXTUAL_TYPES = []

TEXTUAL_TYPES: Tuple[Type, ...] = tuple(
    DEFAULT_TEXTUAL_TYPES + DJANGO_TEXTUAL_TYPES)

try:  # pragma: no cover
    import ujson
except ImportError:
    ujson = None

try:  # pragma: no cover
    import simplejson as json

    # simplejson converts Decimal to float by default, i.e. before
    # we have a chance to override it using Encoder.default.
    _JSON_DEFAULT_KWARGS = {'use_decimal': False}
except ImportError:  # pragma: no cover
    import json                              # type: ignore
    _JSON_DEFAULT_KWARGS = {}

__all__ = [
    'JSONEncoder', 'dumps', 'loads', 'str_to_decimal',
]

#: Max length for string to be converted to decimal.
DECIMAL_MAXLEN = 1000


def str_to_decimal(s: str,
                   maxlen: int = DECIMAL_MAXLEN) -> Optional[Decimal]:
    """Convert string to :class:`~decimal.Decimal`.

    Args:
        s (str): Number to convert.
        maxlen (int): Max length of string.  Default is 100.

    Raises:
        ValueError: if length exceeds maximum length, or if value is not
            a valid number (e.g. Inf, NaN or sNaN).

    Returns:
        Decimal: Converted number.
    """
    if s is None:
        return None
    if len(s) > maxlen:
        raise ValueError(
            f'string of length {len(s)} is longer than limit ({maxlen})')
    v = Decimal(s)
    if not v.is_finite():  # check for Inf/NaN/sNaN/qNaN
        raise ValueError(f'Illegal value in decimal: {s!r}')
    return v


class JSONEncoder(json.JSONEncoder):
    """JSON Encoder.

    Version of JSONEncoder that doesn't strip away microsecond
    information.
    """

    def default(self, o: Any,
                *,
                sequences: Tuple[type, ...] = (set,),
                dates: Tuple[type, ...] = (datetime.date, datetime.time),
                textual: Tuple[type, ...] = TEXTUAL_TYPES) -> Any:
        if isinstance(o, dates):
            if not isinstance(o, (datetime.datetime, datetime.time)):
                o = datetime.datetime(o.year, o.month, o.day, 0, 0, 0, 0)
            r = o.isoformat()
            if r.endswith('+00:00'):
                r = r[:-6] + 'Z'
            return r
        elif isinstance(o, sequences):
            return list(o)
        elif isinstance(o, textual):
            return str(o)
        else:
            return super(JSONEncoder, self).default(o)


if ujson is not None:
    def dumps(obj: Any, **kwargs: Any) -> str:
        return json.dumps(obj)

    def loads(s: str, **kwargs: Any) -> Any:
        return json.loads(obj)
else:
    def dumps(obj: Any,
              cls: Type[JSONEncoder] = JSONEncoder, **kwargs: Any) -> str:
        """Serialize to json.  See :func:`json.dumps`."""
        return json.dumps(obj, cls=cls, **_JSON_DEFAULT_KWARGS, **kwargs)

    def loads(s: str, **kwargs: Any) -> Any:
        """Deserialize json string.  See :func:`json.loads`."""
        return json.loads(s, **kwargs)
