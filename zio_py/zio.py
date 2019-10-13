from dataclasses import dataclass
from typing import Any, Callable, Generic, NoReturn, TypeVar

from zio_py.cause import Cause


A = TypeVar('A', covariant=True)
E = TypeVar('E', covariant=True)
R = TypeVar('R', contravariant=True)

B = TypeVar('B')

# Some invariant analogues of the above types
A0 = TypeVar('A0')
A1 = TypeVar('A1')
E1 = TypeVar('E1')
R1 = TypeVar('R1')


class ZIO(Generic[R, E, A]):
    def flat_map(self: 'ZIO[R1, E1, A]', k: Callable[[A], 'ZIO[R1, E1, B]']) -> 'ZIO[R1, E1, B]':
        return FlatMap(self, k)

    def fold(self, failure: Callable[[E], B], success: Callable[[A], B]) -> 'ZIO[R, NoReturn, B]':
        x: MapFn[R, NoReturn, E, B] = MapFn(failure)
        y: MapFn[R, NoReturn, A, B] = MapFn(success)
        return self.fold_m(x, y)

    def fold_m(self, failure: Callable[[E], 'ZIO[R, E1, B]'],
               success: Callable[[A], 'ZIO[R, E1, B]']) -> 'ZIO[R, E1, B]':
        return self.fold_cause_m(FoldCauseMFailureFn(failure), success)

    def fold_cause_m(self, failure: Callable[[Cause[E]], 'ZIO[R, E1, B]'],
                     success: Callable[[A], 'ZIO[R, E1, B]']) -> 'ZIO[R, E1, B]':
        return Fold(self, failure, success)

    def map(self, f: Callable[[A], B]) -> 'ZIO[R, E, B]':
        g = self._map_helper(f)
        return FlatMap(self, g)

    def _map_helper(self, f: Callable[[A1], B]) -> Callable[[A1], 'ZIO[R, E, B]']:
        return lambda x: ZIOStatic.succeed(f(x))

    def provide(self, r: R) -> 'IO[E, A]':
        return ZIOStatic.provide(r)(self)

    def __invert__(self) -> A:
        pass

# NOTE: Putting these static methods in a different class to avoid name clashes.
# It would be nice to put them in the ZIO class, but...Python.
class ZIOStatic:
    @staticmethod
    def access(f: Callable[[R1], A1]) -> 'ZIO[R1, NoReturn, A1]':
        return Read(lambda r: ZIOStatic.succeed(f(r)))

    @staticmethod
    def access_m(f: Callable[[R], 'ZIO[R, E, A]']) -> 'ZIO[R, E, A]':
        return Read(f)

    @staticmethod
    def effect(effect: Callable[[], A]) -> 'Task[A]':
        return EffectPartial(effect)

    @staticmethod
    def effect_total(effect: Callable[[], A]) -> 'UIO[A]':
        return EffectTotal(effect)

    @staticmethod
    def environment() -> ZIO[R1, NoReturn, R1]:
        return ZIOStatic.access(lambda r: r)

    @staticmethod
    def halt(cause: Cause[E1]) -> 'IO[E1, NoReturn]':
        return Fail(lambda: cause)

    @staticmethod
    def provide(r: R1) -> Callable[['ZIO[R1, E1, A1]'], 'IO[E1, A1]']:
        return lambda zio: Provide(r, zio)

    @staticmethod
    def succeed(a: A1) -> 'UIO[A1]':
        return Succeed(a)


RIO = ZIO[R, Exception, A]
URIO = ZIO[R, NoReturn, A]
IO = ZIO[Any, E, A]
UIO = ZIO[Any, NoReturn, A]
Task = ZIO[Any, Exception, A]


class EffectPartial(Generic[A], Task[A]):
    def __init__(self, effect: Callable[[], A]) -> None:
        self.effect = effect


class EffectTotal(Generic[A], UIO[A]):
    def __init__(self, effect: Callable[[], A]) -> None:
        self.effect = effect


@dataclass(frozen=True)
class Fail(Generic[E, A], IO[E, A]):
    cause: Callable[[], Cause[E]]


class FlatMap(Generic[R, E1, A0, A1], ZIO[R, E1, A1]):
    def __init__(self, zio: ZIO[R, E1, A0], k: Callable[[A0], ZIO[R, E1, A1]]) -> None:
        self._zio = zio
        self._k = k

    @property
    def zio(self) -> ZIO[R, E1, A0]:
        return self._zio

    @property
    def k(self) -> Callable[[A0], ZIO[R, E1, A1]]:
        return self._k


class Fold(Generic[R, E, E1, A1, B], ZIO[R, E1, B]):
    def __init__(
        self,
        value: ZIO[R, E, A1],
        failure: Callable[[Cause[E]], ZIO[R, E1, B]],
        success: Callable[[A1], ZIO[R, E1, B]]
    ) -> None:
        self._value = value
        self._failure = failure
        self._success = success

    @property
    def value(self) -> ZIO[R, E, A1]:
        return self._value

    @property
    def failure(self) -> Callable[[Cause[E]], ZIO[R, E1, B]]:
        return self._failure

    @property
    def success(self) -> Callable[[A1], ZIO[R, E1, B]]:
        return self._success

    def __call__(self, v: A1) -> ZIO[R, E1, B]:
        return self.success(v)


class FoldCauseMFailureFn(Generic[R, E, E1, A]):
    def __init__(self, underlying: Callable[[E], ZIO[R, E1, A]]):
        self._underlying = underlying

    def __call__(self, c: Cause[E]) -> ZIO[R, E1, A]:
        return c.failure_or_cause().fold(self._underlying, ZIOStatic.halt)


class MapFn(Generic[R1, E1, A1, B], ZIO[R1, E1, B]):
    def __init__(self, underlying: Callable[[A1], B]) -> None:
        self._underlying = underlying

    def __call__(self, a: A1) -> ZIO[R1, E1, B]:
        return Succeed(self._underlying(a))


@dataclass(frozen=True)
class Provide(Generic[R, E, A], IO[E, A]):
    r: R
    next: ZIO[R, E, A]


class Read(Generic[R, E, A], ZIO[R, E, A]):
    def __init__(self, k: Callable[[R], ZIO[R, E, A]]):
        self._k = k

    @property
    def k(self) -> Callable[[R], ZIO[R, E, A]]:
        return self._k


@dataclass(frozen=True)
class Succeed(Generic[A], UIO[A]):
    value: A
