from typing import override

from trad.kernel.boundaries.pipes import Pipe, RouteInstanceId, SummitInstanceId
from trad.kernel.entities import Post, Route, Summit
from trad.kernel.errors import EntityNotFoundError


class CollectedData(Pipe):
    def __init__(self) -> None:
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
