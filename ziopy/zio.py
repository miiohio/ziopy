import functools
from dataclasses import dataclass
from typing import Callable, Generic, NoReturn, Tuple, Type, TypeVar, Union

from ziopy.either import Either, Left, Right

"""
Heavily inspired by:
https://github.com/jdegoes/functional-effects/blob/master/src/main/scala/net/degoes/zio/00-intro.scala
"""


R = TypeVar('R', contravariant=True)
E = TypeVar('E', covariant=True)
A = TypeVar('A', covariant=True)
B = TypeVar('B')

G = TypeVar('G', bound=BaseException, covariant=True)

RR = TypeVar('RR')
EE = TypeVar('EE')
AA = TypeVar('AA')
BB = TypeVar('BB')

E2 = TypeVar('E2')
A2 = TypeVar('A2')

T = TypeVar('T')
Thunk = Callable[[], T]

F = TypeVar('F', bound=Callable)

X = TypeVar('X', bound=BaseException)


def _raise(x: X) -> NoReturn:
    raise x


@dataclass(frozen=True)
class TypeMatchException(Generic[AA], Exception):
    value: AA


class ZIO(Generic[R, E, A]):
    def __init__(self, run: Callable[[R], Either[E, A]]):
        self._run = run

    @staticmethod
    def succeed(a: AA) -> "ZIO[object, NoReturn, AA]":
        return ZIO(lambda _: Right(a))

    @staticmethod
    def fail(e: EE) -> "ZIO[object, EE, NoReturn]":
        return ZIO(lambda _: Left(e))

    @staticmethod
    def from_either(e: Either[E, A]) -> "ZIO[object, E, A]":
        return ZIO(lambda _: e)

    @staticmethod
    def effect(side_effect: Thunk[A]) -> "ZIO[object, Exception, A]":
        a = ZIO[object, NoReturn, A](lambda _: Either.right(side_effect()))
        return a.catch(Exception)

    @staticmethod
    def effect_catch(side_effect: Thunk[A], exception_type: Type[X]) -> "ZIO[object, X, A]":
        a = ZIO[object, NoReturn, A](lambda _: Either.right(side_effect()))
        return a.catch(exception_type)

    @staticmethod
    def access(f: Callable[[R], A]) -> "ZIO[R, NoReturn, A]":
        return ZIO(lambda r: Right(f(r)))

    @staticmethod
    def access_m(f: Callable[[R], "ZIO[R, E, A]"]) -> "ZIO[R, E, A]":
        return ZIO(lambda r: f(r)._run(r))

    def provide(self, r: R) -> "ZIO[object, E, A]":
        return ZIO(lambda _: self._run(r))

    @staticmethod
    def effect_total(side_effect: Thunk[A]) -> "ZIO[object, NoReturn, A]":
        return ZIO(lambda _: Right(side_effect()))

    def catch(
        self: "ZIO[R, E, AA]",
        exc: Type[X]
    ) -> "ZIO[R, Union[E, X], AA]":
        def _f(r: R) -> Either[Union[E, X], AA]:
            try:
                return self._run(r)
            except exc as e:
                return Either.left(e)
        return ZIO(_f)

    def map(self, f: Callable[[A], B]) -> "ZIO[R, E, B]":
        return ZIO(lambda r: self._run(r).map(f))

    def map_error(self: "ZIO[RR, EE, AA]", f: Callable[[EE], E2]) -> "ZIO[RR, E2, AA]":
        return ZIO(lambda r: self._run(r).map_left(f))

    def flat_map(
        self: "ZIO[RR, E, AA]",
        f: Callable[[AA], "ZIO[RR, EE, B]"]
    ) -> "ZIO[RR, Union[E, EE], B]":
        return ZIO(lambda r: self._run(r).flat_map(lambda a: f(a)._run(r)))

    def flatten(
        self: "ZIO[R, E, ZIO[R, EE, AA]]"
    ) -> "ZIO[R, Union[E, EE], AA]":
        return self.flat_map(lambda x: x)

    def swap_environments(
        self: "ZIO[R, E, ZIO[RR, EE, AA]]"
    ) -> "ZIO[RR, NoReturn, ZIO[R, Union[E, EE], AA]]":
        """
        Swaps the order of the environments of two nested ZIO instances.

        How it works:
            A `ZIO[R, E, A]` instance is isomorphic to Callable[[R], Either[E, A]].
            So, a ZIO instance that produces another ZIO instance is equivalent to
            a curried function:

                ZIO[R1, E1, ZIO[R2, E2, A]] is equivalent to
                R1 -> Either[E1, (R2 -> Either[E2, A])]

            which, when uncurried, is just a function with two arguments:

                (R1, R2) -> Either[Union[E1, E2], A]

            So we can swap the order of those two parameters freely.

        Author's Note:
            Adding a special method to ZIO for swapping arguments is a bit clumsy;
            there are more elegant/compositional ways for manipulating function
            parameters. Unfortunately `mypy` (as of Jan. 2021) struggles with type
            inference, so we will stick with this special case.
        """
        return Environment[RR]().map(
            lambda rr: ZIO(lambda r: self._run(r).flat_map(lambda inner: inner._run(rr)))
        )

    def __lshift__(self: "ZIO[RR, EE, AA]", other: "ZIO[RR, EE, B]") -> "ZIO[RR, EE, B]":
        return self.flat_map(lambda _: other)

    def zip(
        self: "ZIO[RR, E, AA]",
        that: "ZIO[RR, EE, B]"
    ) -> "ZIO[RR, Union[E, EE], Tuple[AA, B]]":
        return self.flat_map(lambda a: that.map(lambda b: (a, b)))

    def either(self) -> "ZIO[R, NoReturn, Either[E, A]]":
        return ZIO(lambda r: Right(self._run(r)))

    def absolve(self: "ZIO[R, E, Either[EE, AA]]") -> "ZIO[R, Union[E, EE], AA]":
        return self.flat_map(ZIO.from_either)

    def or_die(self: "ZIO[R, X, AA]") -> "ZIO[R, NoReturn, AA]":
        return ZIO(lambda r: self._run(r).fold(_raise, lambda a: Right(a)))

    def require(
        self: "ZIO[R, E, AA]",
        predicate: Callable[[AA], bool],
        to_error: Callable[[AA], EE]
    ) -> "ZIO[R, Union[E, EE], AA]":
        return ZIO(lambda r: self._run(r).require(predicate, to_error))

    def asserting(
        self: "ZIO[R, E, AA]",
        predicate: Callable[[AA], bool],
        to_error: Callable[[AA], X]
    ) -> "ZIO[R, E, AA]":
        return ZIO(lambda r: self._run(r).asserting(predicate, to_error))

    def or_else(
        self: "ZIO[R, EE, AA]",
        other: "ZIO[R, E2, A2]"
    ) -> "ZIO[R, Union[EE, E2], Union[AA, A2]]":
        return ZIO(
            lambda r: self._run(r).fold(
                lambda e: other._run(r),
                lambda a: Right(a)
            )
        )

    def swap(self: "ZIO[R, EE, AA]") -> "ZIO[R, AA, EE]":
        return ZIO(lambda r: self._run(r).swap())

    def match_types(self: "ZIO[R, E, AA]") -> "ZIO[R, E, NoReturn]":
        def _f(arg: AA) -> NoReturn:
            raise TypeMatchException(arg)
        return self.map(_f)

    def at_type(
        self: "ZIO[RR, EE, AA]",
        target_type: Type[A2],
        operation: "ZIO[A2, E2, BB]"
    ) -> "ZIO[RR, Union[EE, E2], Union[AA, BB]]":
        def _recover(arg: Union[EE, TypeMatchException]) -> ZIO[object, Union[EE, E2], BB]:
            if not isinstance(arg, TypeMatchException):
                return ZIO.fail(arg)
            if isinstance(arg.value, target_type):
                return operation.provide(arg.value)
            else:
                raise arg from arg

        return (
            self
            .catch(TypeMatchException)
            .swap()
            .either()
            .flat_map(lambda e: e.fold(ZIO.succeed, _recover))
        )

    def to_callable(
        self: "ZIO[FunctionArguments[F], NoReturn, AA]"
    ) -> "Callable[..., AA]":
        """
        Converts this ZIO instance into a Callable. This conversion is an
        isomorphism whose inverse is `ZIO.from_callable`.
        """
        return (
            lambda *args, **kwargs:
            self.provide(FunctionArguments(*args, **kwargs))._run(None).to_right().value
        )

    @staticmethod
    def from_callable(
        func: F
    ) -> "ZIO[FunctionArguments[F], NoReturn, A]":
        """
        Converts the given function (Callable) into a ZIO instance. This conversion
        is an isomorphism whose inverse is `ZIO.to_callable`.
        """
        return (
            Environment[FunctionArguments[F]]()
            .map(lambda func_args: func(*func_args.args, **func_args.kwargs))
        )


class Environment(Generic[R], ZIO[R, NoReturn, R]):
    def __init__(self) -> None:
        self._run = lambda r: Right(r)


def unsafe_run(io: ZIO[object, X, AA]) -> AA:
    return io._run(None).fold(_raise, lambda a: a)


@dataclass(frozen=True)
class _RaiseLeft(Generic[E], Exception):
    value: E


class ZIOMonad(Generic[R, EE]):
    def __init__(self, environment: R) -> None:
        self._environment = environment

    def __lshift__(self, arg: ZIO[R, EE, BB]) -> BB:
        return arg._run(self._environment).fold(
            lambda e: _raise(_RaiseLeft(e)),
            lambda a: a
        )


def monadic(func: F) -> F:
    @functools.wraps(func)
    def _wrapper(*args: object, **kwargs: object) -> object:
        def _catch_left(environment: R) -> ZIO[R, E, A]:
            try:
                return func(do=ZIOMonad(environment), *args, **kwargs)
            except _RaiseLeft as raise_left:
                # NOTE: WJH (12/20/20) mypy can't prove that the generic type
                #       of the _RaiseLeft instance here is `E`, so we have to
                #       use `type: ignore`.
                return ZIO.fail(raise_left.value)  # type: ignore

        return Environment().flat_map(_catch_left)
    return _wrapper  # type: ignore


class FunctionArguments(Generic[F]):
    """
    A simple container that represents the inputs to an arbitrary Python
    function (via *args, **kwargs). The type parameter "F" represents the precise
    type of the function for which these arguments are intended.
    """
    def __init__(self, *args: object, **kwargs: object) -> None:
        self.args = args
        self.kwargs = kwargs
