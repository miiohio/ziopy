from dataclasses import dataclass
from typing import Generic, NoReturn, TypeVar
from typing_extensions import Final

from ziopy.either import Either, Left, Right
from ziopy.zio import ZIO, monadic, ZIOMonad, unsafe_run, _raise

R = TypeVar('R')
E = TypeVar('E', bound=BaseException)
A = TypeVar('A')


@dataclass(frozen=True)
class Bippy(Exception):
    pass


@dataclass(frozen=True)
class NotBippy(Exception):
    pass


@dataclass(frozen=True)
class Equiv(Generic[R, E, A]):
    """
    Witnesses the following equivalence relation:
    Inputs:
    1. A ZIO program "p" written using combinator syntax
    2. A ZIO program "q" written using ZIOMonad
    3. An environment that will be provided as input to both programs.
    4. The expected output of `unsafe_run` of both programs, where:
        Right(_) indicates success, and
        Left(_) indicates that an uncaught exception was raised.
    """

    p: ZIO[R, E, A]
    q: ZIO[R, E, A]
    environment: R
    expected_output: Either[E, A]

    def is_satisfied(self) -> bool:
        output_p = unsafe_run(self.p.either().provide(self.environment))
        output_q = unsafe_run(self.q.either().provide(self.environment))
        return output_p == output_q == self.expected_output


@monadic
def _q1(do: ZIOMonad[object, NoReturn]) -> ZIO[object, NoReturn, int]:
    result = do << ZIO.succeed(42)
    return ZIO.succeed(result)


EQ1: Final = Equiv(ZIO.succeed(42), _q1(), (), Right(42))


@monadic
def _q2(do: ZIOMonad[object, NoReturn]) -> ZIO[object, NoReturn, int]:
    result = do << ZIO.succeed(42)
    return ZIO.succeed(result)


EQ2: Final = Equiv(ZIO.succeed(42), _q2(), (), Right(42))


@monadic
def _q3(do: ZIOMonad[object, Bippy]) -> ZIO[object, Bippy, int]:
    do << ZIO.fail(Bippy())
    return ZIO.succeed(42)


EQ3: Final = Equiv(ZIO.fail(Bippy()), _q3(), (), Left(Bippy()))


@monadic
def _q4(do: ZIOMonad[object, Exception]) -> ZIO[object, Exception, int]:
    result = do << ZIO.effect(lambda: 42)
    return ZIO.succeed(result)


EQ4: Final = Equiv(ZIO.effect(lambda: 42), _q4(), (), Right(42))


@monadic
def _q5(do: ZIOMonad[object, Exception]) -> ZIO[object, Exception, int]:
    do << ZIO.effect(lambda: _raise(Bippy()))  # type: ignore
    return ZIO.succeed(42)


EQ5: Final = Equiv(ZIO.effect(lambda: _raise(Bippy())), _q5(), (), Left(Bippy()))


@monadic
def _q6(do: ZIOMonad[object, Bippy]) -> ZIO[object, Bippy, int]:
    result = do << ZIO.effect_catch(lambda: _raise(Bippy()), Bippy)  # type: ignore
    return ZIO.succeed(result)


EQ6: Final = Equiv(ZIO.effect_catch(lambda: _raise(Bippy()), Bippy), _q6(), None, Left(Bippy()))


@monadic
def _q7(do: ZIOMonad[object, NotBippy]) -> ZIO[object, NotBippy, int]:
    result: int = do << (
        ZIO.effect_catch(lambda: _raise(Bippy()), NotBippy).catch(Bippy)  # type: ignore
    )
    return ZIO.succeed(result)


EQ7: Final = Equiv(
    ZIO.effect_catch(lambda: _raise(Bippy()), NotBippy).catch(Bippy),  # type: ignore
    _q7(),
    None,
    Left(Bippy())
)
