import re
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Pattern, Tuple, Union

#: Alias for things that can be added to a router.
RouteLike = Union["Route", "Include"]


class Route:
    """An individual route.
    """

    __slots__ = [
        "template",
        "handler",
        "method",
        "name",
    ]

    def __init__(self, template: str, handler: Callable[..., Any], method: str = "GET", name: Optional[str] = None) -> None:
        self.template = template
        self.handler = handler
        self.method = method
        self.name = name or handler.__name__


class Include:
    """Groups of routes prefixed by a common path.
    """

    __slots__ = [
        "prefix",
        "routes",
    ]

    def __init__(self, prefix: str, routes: List[RouteLike]) -> None:
        self.prefix = prefix
        self.routes = routes


class Router:
    """A collection of routes.
    """

    def __init__(self, routes: Optional[List[RouteLike]] = None) -> None:
        self._routes_by_name: Dict[str, Route] = {}
        self._routes_by_method: Dict[str, List[Route]] = defaultdict(list)
        self._route_res_by_method: Dict[str, List[Pattern[str]]] = defaultdict(list)
        self.add_routes(routes or [])

    def add_route(self, route_like: RouteLike, prefix: str = "") -> None:
        """Add a Route to this instance.
        """
        if isinstance(route_like, Include):
            self.add_routes(route_like.routes, prefix + route_like.prefix)

        elif isinstance(route_like, Route):
            if route_like.name in self._routes_by_name:
                raise ValueError(f"a route named {route_like.name} is already registered")

            self._routes_by_name[route_like.name] = route_like
            self._routes_by_method[route_like.method].insert(0, route_like)
            self._route_res_by_method[route_like.method].insert(
                0, _compile_route_template(prefix + route_like.template),
            )

        else:  # pragma: no cover
            raise NotImplementedError(f"unhandled type {type(route_like)}")

    def add_routes(self, route_likes: List[RouteLike], prefix: str = "") -> None:
        """Add a set of routes to this instance.
        """
        for route_like in route_likes:
            self.add_route(route_like, prefix)

    def match(self, method: str, path: str) -> Union[None, Tuple[Route, Dict[str, str]]]:
        """Look up the route matching the given method and path.
        Returns the route and any path params.
        """
        routes = self._routes_by_method[method]
        route_res = self._route_res_by_method[method]
        for route, route_re in zip(routes, route_res):
            match = route_re.match(path)
            if match is not None:
                return route, match.groupdict()

        return None


def _compile_route_template(template: str) -> Pattern[str]:
    """Convert a route template into a regular expression.
    """
    re_template = ""
    for segment in template.split("/")[1:]:
        if segment.startswith("{") and segment.endswith("}"):
            segment_name = segment[1:-1]
            re_template += f"/(?P<{segment_name}>[^/]+)"
        else:
            re_template += f"/{segment}"

    return re.compile(f"^{re_template}$")