from typing import Dict, List, Optional, Union
from urllib.parse import parse_qsl

from ..common import MultiDict
from ..errors import ParamMissing
from ..typing import Environ

ParamsDict = Dict[str, Union[str, List[str]]]


class QueryParams(MultiDict[str, str]):
    """A mapping from param names to lists of values.  Once
    constructed, these instances cannot be modified.
    """

    @classmethod
    def from_environ(cls, environ: Environ) -> "QueryParams":
        """Construct a QueryParams instance from a WSGI environ.
        """
        return cls.parse(environ["QUERY_STRING"])

    @classmethod
    def parse(cls, query_string: str) -> "QueryParams":
        """Construct a QueryParams instance from a query string.
        """
        return cls(parse_qsl(query_string))

    def get(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get the last value for a given key.
        """
        try:
            return self[name]
        except ParamMissing:
            return default

    def __getitem__(self, name: str) -> str:
        """Get the last value for a given key.

        Raises:
          ParamMissing: When the key is missing.
        """
        try:
            return self._data[name][-1]
        except IndexError:
            raise ParamMissing(name)
