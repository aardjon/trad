"""
Implementation of the Pipe interface.
"""

from collections.abc import Iterator
from typing import override

from trad.kernel.boundaries.pipes import Pipe, PipeFactory, RouteInstanceId, SummitInstanceId
from trad.kernel.entities import Post, Route, Summit
from trad.kernel.errors import EntityNotFoundError


class CollectedData(Pipe):
    """
    The default Pipe implementation that simply stores all data created by a single filter stage.
    """

    def __init__(self) -> None:
        """Initialize a new CollectedData instance."""
        self._summits: list[Summit] = []
        self._routes: list[Route] = []
        self._posts: list[Post] = []

        self._routes2summits: dict[SummitInstanceId, list[RouteInstanceId]] = {}
        self._posts2routes: dict[RouteInstanceId, list[int]] = {}

    @override
    def add_summit(self, summit: Summit) -> SummitInstanceId:
        self._summits.append(summit)
        return SummitInstanceId(len(self._summits) - 1)

    @override
    def add_route(self, summit_id: SummitInstanceId, route: Route) -> RouteInstanceId:
        if summit_id < 0 or not summit_id < len(self._summits):
            raise EntityNotFoundError(f"Summit #{summit_id}")

        self._routes.append(route)
        route_id = RouteInstanceId(len(self._routes) - 1)
        self._routes2summits.setdefault(summit_id, []).append(route_id)
        return route_id

    @override
    def add_post(self, route_id: RouteInstanceId, post: Post) -> None:
        if route_id < 0 or not route_id < len(self._routes):
            raise EntityNotFoundError(f"Route #{route_id}")

        self._posts.append(post)
        post_idx = len(self._posts) - 1
        self._posts2routes.setdefault(route_id, []).append(post_idx)

    @override
    def iter_summits(self) -> Iterator[tuple[SummitInstanceId, Summit]]:
        yield from enumerate(self._summits)

    @override
    def iter_routes_of_summit(
        self, summit_id: SummitInstanceId
    ) -> Iterator[tuple[RouteInstanceId, Route]]:
        route_ids = self._routes2summits.get(summit_id, [])
        yield from ((route_idx, self._routes[route_idx]) for route_idx in route_ids)

    @override
    def iter_posts_of_route(self, route_id: RouteInstanceId) -> Iterator[Post]:
        post_ids = self._posts2routes.get(route_id, [])
        yield from (self._posts[post_id] for post_id in post_ids)


class AllPipesFactory(PipeFactory):
    """
    PipeFactory implementation for creating the correct pipes for all stages.
    """

    @override
    def create_pipe(self) -> Pipe:
        return CollectedData()
