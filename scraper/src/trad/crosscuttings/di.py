"""
Dependency injection package to be used by all parts of the trad scraper application.

To simplify things, the public interface shall be kept as similar as possible to its Dart
counterpart.
"""

from typing import Callable, TypeVar

from lidipy import Lidi
from lidipy.exceptions import BindingMissing

from trad.crosscuttings.errors import InvalidStateError

_InterfaceType = TypeVar("_InterfaceType")
""" The interface type being registered or requested. """


class DependencyProvider:
    """
    Central entry point for registering or retrieving the concrete boundary implementations.

    Usage example:
    ```python
    DependencyProvider di = DependencyProvider();
    StorageBoundary storage = di.provide(StorageBoundary);
    ```

    This class is not a singleton but all instances share the same DI configuration, so they can be
    created on demand as needed. Most system parts will only ever need the [provide()] method.
    """

    _lidi_instance = Lidi()

    def provide(self, interface_class: type[_InterfaceType]) -> _InterfaceType:
        """
        Returns the concrete implementation for the interface requested by [interface_class].

        Throws [InvalidStateError] if the requested interface has not been [register()]ed
        before.
        """
        try:
            return DependencyProvider._lidi_instance.resolve(interface_class)
        except BindingMissing as e:
            raise InvalidStateError(
                f"No implementation is available for the requested interface {interface_class}"
            ) from e

    def register_factory(
        self,
        interface_class: type[_InterfaceType],
        instance_factory: Callable[[], _InterfaceType],
    ) -> None:
        """
        Registers a factory for creating new implementations of the interface [interface_class].

        Any previous implementation registration for [interface_class] is discarded.

        The [instance_factory] is a functor that must return a new instance of [interface_class]. It
        is called once for each [provide(interface_class)] call, creating (and thus, providing) a
        new implementation instance each time.

        Registration should be done only once during start up from within `trad.main`.
        """
        DependencyProvider._lidi_instance.bind(interface_class, instance_factory, singleton=False)

    def register_singleton(
        self,
        interface_class: type[_InterfaceType],
        instance_factory: Callable[[], _InterfaceType],
    ) -> None:
        """
        Registers a singleton implementation of the interface [interface_class].

        Any previous implementation registration for [interface_class] is discarded.

        The [instance_factory] is a functor that must return a new instance of [interface_class]. It
        is called at any time but exactly once, at the latest when the implementation is requested
        for the first time. Each [provide(interface_class)] call returns the same implementation
        instance.

        Registration should be done only once during start up from within `trad.main`.
        """
        DependencyProvider._lidi_instance.bind(interface_class, instance_factory, singleton=True)

    def shutdown(self) -> None:
        """
        Cleans up the DI registry by removing all registrations at once.

        This should only be called during shutdown from within `trad.main`.
        """
        DependencyProvider._lidi_instance = Lidi()
