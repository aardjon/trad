"""
Unit tests for the trad.crosscuttings.di module.
"""

from abc import ABCMeta

import pytest

from trad.crosscuttings.di import DependencyProvider
from trad.crosscuttings.errors import InvalidStateException


class ExampleInterface1(metaclass=ABCMeta): ...


class ExampleInterface2(metaclass=ABCMeta): ...


class ExampleImpl(ExampleInterface1): ...


class TestDependencyProvider:
    """
    Unit tests for the DependencyProvider class.
    """

    def teardown(self) -> None:
        DependencyProvider().shutdown()

    def test_provide(self) -> None:
        """
        Ensure the correct behaviour of the provide() method:
         - Return the registered implementation, if any
         - Throw if the requested interface has not been registered
        """
        di = DependencyProvider()
        di.registerFactory(ExampleInterface1, lambda: ExampleImpl())

        assert isinstance(di.provide(ExampleInterface1), ExampleImpl)
        with pytest.raises(InvalidStateException):
            di.provide(ExampleInterface2)

    def test_factory(self) -> None:
        """
        Ensure the correct behaviour for registered factories: The factory must be executed on each
        provide() call, returning a new interface implementation instance each time.
        """
        di = DependencyProvider()
        di.registerFactory(ExampleInterface1, lambda: ExampleImpl())

        impl1 = di.provide(ExampleInterface1)
        impl2 = di.provide(ExampleInterface1)
        assert impl1 is not None
        assert impl2 is not None
        assert id(impl1) != id(impl2)

    def test_singleton(self) -> None:
        """
        Ensure the correct behaviour for registered singletons: The factory must be executed exactly
        once, and each provide() call must return the same implementation.
        """
        di = DependencyProvider()
        di.registerSingleton(ExampleInterface1, lambda: ExampleImpl())

        impl1 = di.provide(ExampleInterface1)
        impl2 = di.provide(ExampleInterface1)
        assert impl1 is not None
        assert id(impl1) == id(impl2)

    def test_shared_configuration(self) -> None:
        """
        Ensure that all instances share the same DI configuration: A different instance must return
        the registered implementation, too.
        """
        di1 = DependencyProvider()
        di2 = DependencyProvider()

        # Register an implementation on the first instance...
        di1.registerFactory(ExampleInterface1, lambda: ExampleImpl())
        # ...and get it from the second one
        assert isinstance(di2.provide(ExampleInterface1), ExampleImpl)

    def test_shutdown(self) -> None:
        """
        Ensure that calling shutdown() really discards all bindings.
        """
        di = DependencyProvider()
        di.registerSingleton(ExampleInterface1, lambda: ExampleImpl())
        di.shutdown()
        # Now there mustn't be a binding for ExampleInterface1 anymore
        with pytest.raises(InvalidStateException):
            di.provide(ExampleInterface1)
