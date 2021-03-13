from dataclasses import dataclass
from typing import Callable, NoReturn, Optional, Set, TypeVar, Union

import pytest

from . import zio_equivalence_relations as eqr
from zio_py.either import Either, Left, Right
from zio_py.zio import (
    Environment, TypeMatchException, ZIO, unsafe_run, _raise, FunctionArguments
)

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
class FooException(Exception):
    foo: str


@dataclass(frozen=True)
class BarException(Exception):
    bar: str


def test_zio_raise() -> None:
    with pytest.raises(Bippy):
        _raise(Bippy())


def test_zio_constructor() -> None:
    def _f(i: int) -> Either[Exception, str]:
        return Either.right(str(i))

    assert ZIO(_f)._run == _f


def test_zio_succeed() -> None:
    assert ZIO.succeed(42)._run(()) == Right(42)


def test_zio_fail() -> None:
    assert ZIO.fail(42)._run(()) == Left(42)


def test_zio_effect_success() -> None:
    x: Optional[int] = None

    def _impure_function() -> None:
        nonlocal x
        x = 42

    program = ZIO.effect(_impure_function)
    assert x is None

    program._run(())
    assert x == 42


def test_zio_effect_failure() -> None:

    def _impure_function() -> None:
        raise Bippy

    program = ZIO.effect(_impure_function)
    assert program._run(()) == Left(Bippy())


def test_zio_effect_catch_1() -> None:
    x: Optional[int] = None

    def _impure_function() -> int:
        nonlocal x
        x = 100
        return 42

    program = ZIO.effect_catch(_impure_function, Bippy)
    assert x is None
    assert program._run(()) == Right(42)
    assert x == 100


def test_zio_effect_catch_2() -> None:
    def _impure_function() -> None:
        raise Bippy

    program = ZIO.effect_catch(_impure_function, Bippy)
    assert program._run(()) == Left(Bippy())


def test_zio_effect_catch_3() -> None:
    def _impure_function() -> None:
        raise Bippy

    program = ZIO.effect_catch(_impure_function, NotBippy)
    with pytest.raises(Bippy):
        program._run(())


def test_zio_access() -> None:
    accessor: Callable[[str], int] = len
    assert ZIO.access(accessor)._run("hello") == Right(5)


def test_zio_access_m_1() -> None:
    accessor: Callable[[str], ZIO[object, NoReturn, int]] = lambda s: ZIO.succeed(len(s))
    assert ZIO.access_m(accessor)._run("hello") == Right(5)


def test_zio_access_m_2() -> None:
    accessor: Callable[[str], ZIO[object, str, int]] = lambda s: ZIO.fail("oops")
    assert ZIO.access_m(accessor)._run("hello") == Left("oops")


def test_zio_provide() -> None:
    assert (
        ZIO(Right[int])
        .map(lambda x: x + 1)
        .map(lambda x: x + 1)
        .map(lambda x: x + 1)
        .provide(100)
        ._run(())
    ) == Right(103)


def test_zio_effect_total() -> None:
    x: Optional[int] = None

    def _impure_function() -> None:
        nonlocal x
        x = 42

    program = ZIO.effect_total(_impure_function)
    assert x is None

    program._run(())
    assert x == 42


def test_zio_catch_1() -> None:
    x: Optional[int] = None

    def _impure_function() -> int:
        nonlocal x
        x = 100
        return 42

    program = ZIO.effect(_impure_function).catch(NotBippy)
    assert x is None
    assert program._run(()) == Right(42)
    assert x == 100


def test_zio_catch_2() -> None:
    def _impure_function() -> int:
        raise Bippy

    program = ZIO.effect(_impure_function).catch(Bippy)
    assert program._run(()) == Left(Bippy())


def test_zio_catch_3() -> None:
    def _impure_function() -> int:
        raise Bippy

    program = ZIO.effect_total(_impure_function).catch(NotBippy)
    with pytest.raises(Bippy):
        program._run(())


def test_zio_map_1() -> None:
    count = 0

    def _impure_function(x: int) -> int:
        nonlocal count
        count += 1
        return x + 1

    assert (
        ZIO.succeed(100)
        .map(_impure_function)
        .map(_impure_function)
        .map(_impure_function)
        .map(lambda x: f"The result is: {x}")
        ._run(())
    ) == Right("The result is: 103")
    assert count == 3


def test_zio_map_2() -> None:
    count = 0

    def _impure_function(x: int) -> int:
        nonlocal count
        count += 1
        return x + 1

    def _kaboom(x: int) -> int:
        raise Bippy

    assert (
        ZIO.succeed(100)
        .map(_impure_function)
        .map(_kaboom)
        .map(_impure_function)
        .map(_impure_function)
        .map(lambda x: f"The result is: {x}")
        .catch(Bippy)
        ._run(())
    ) == Left(Bippy())
    assert count == 1


def test_zio_map_error_1() -> None:
    count = 0

    def _impure_function(x: int) -> int:
        nonlocal count
        count += 1
        return x + 1

    assert (
        ZIO.fail(100)
        .map_error(_impure_function)
        .map_error(_impure_function)
        .map_error(_impure_function)
        .map_error(lambda x: f"The result is: {x}")
        ._run(())
    ) == Left("The result is: 103")
    assert count == 3


def test_zio_map_error_2() -> None:
    count = 0

    def _impure_function(x: int) -> int:
        nonlocal count
        count += 1
        return x + 1

    def _kaboom(x: int) -> int:
        raise Bippy

    assert (
        ZIO.fail(100)
        .map_error(_impure_function)
        .map_error(_kaboom)
        .map_error(_impure_function)
        .map_error(_impure_function)
        .map_error(lambda x: f"The result is: {x}")
        .catch(Bippy)
        ._run(())
    ) == Left(Bippy())
    assert count == 1


def test_zio_flat_map_1() -> None:
    count = 0

    def _impure_function(x: int) -> ZIO[object, NoReturn, int]:
        nonlocal count
        count += 1
        return ZIO.succeed(x + 1)

    assert (
        ZIO.succeed(100)
        .flat_map(_impure_function)
        .flat_map(_impure_function)
        .flat_map(_impure_function)
        .flat_map(lambda x: ZIO.succeed(f"The result is: {x}"))
        ._run(())
    ) == Right("The result is: 103")
    assert count == 3


def test_zio_flat_map_2() -> None:
    count = 0

    def _impure_function(x: int) -> ZIO[object, NoReturn, int]:
        nonlocal count
        count += 1
        return ZIO.succeed(x + 1)

    def _kaboom(x: int) -> ZIO[object, NoReturn, int]:
        raise Bippy

    assert (
        ZIO.succeed(100)
        .flat_map(_impure_function)
        .flat_map(_kaboom)
        .flat_map(_impure_function)
        .flat_map(_impure_function)
        .flat_map(lambda x: ZIO.succeed(f"The result is: {x}"))
        .catch(Bippy)
        ._run(())
    ) == Left(Bippy())
    assert count == 1


def test_zio_flatten_1() -> None:
    count = 0

    def _impure_function(x: int) -> ZIO[object, NoReturn, int]:
        nonlocal count
        count += 1
        return ZIO.succeed(x + 1)

    assert (
        ZIO.succeed(100)
        .flat_map(_impure_function)
        .flat_map(_impure_function)
        .flat_map(_impure_function)
        .map(lambda x: ZIO.succeed(f"The result is: {x}"))
        .flatten()
        ._run(())
    ) == Right("The result is: 103")
    assert count == 3


def test_zio_flatten_2() -> None:
    count = 0

    def _impure_function(x: int) -> ZIO[object, NoReturn, int]:
        nonlocal count
        count += 1
        return ZIO.succeed(x + 1)

    def _kaboom(x: int) -> ZIO[object, NoReturn, int]:
        raise Bippy

    assert (
        ZIO.succeed(100)
        .flat_map(_impure_function)
        .flat_map(_kaboom)
        .flat_map(_impure_function)
        .flat_map(_impure_function)
        .map(lambda x: ZIO.succeed(f"The result is: {x}"))
        .catch(Bippy)
        .flatten()
        ._run(())
    ) == Left(Bippy())
    assert count == 1


def test_zio_lshift_1() -> None:
    assert (
        ZIO.succeed(100)
        << ZIO.succeed(1)
        << ZIO.succeed(2)
        << ZIO.succeed(3)
    ).flat_map(
        lambda x: ZIO.succeed(f"The result is: {x}")
    )._run(()) == Right("The result is: 3")


def test_zio_lshift_2() -> None:
    def _kaboom(x: object) -> Either[NoReturn, int]:
        raise Bippy

    assert (
        (
            ZIO.succeed(100)
            << ZIO.succeed(1)
            << ZIO.succeed(2)
            << ZIO(_kaboom)
            << ZIO.succeed(3)
        )
        .flat_map(lambda x: ZIO.succeed(f"The result is: {x}"))
        .catch(Bippy)
    )._run(()) == Left(Bippy())


def test_zio_zip_1() -> None:
    assert ZIO.succeed("a").zip(ZIO.succeed(42))._run(()) == Right(("a", 42))


def test_zio_zip_2() -> None:
    assert ZIO.fail("a").zip(ZIO.succeed(42))._run(()) == Left("a")


def test_zio_zip_3() -> None:
    assert ZIO.succeed("a").zip(ZIO.fail(42))._run(()) == Left(42)


def test_zio_either_1() -> None:
    assert ZIO.succeed("a").either()._run(()) == Right(Right("a"))


def test_zio_either_2() -> None:
    assert ZIO.fail("a").either()._run(()) == Right(Left("a"))


def test_zio_or_die_1() -> None:
    assert ZIO.succeed(42).or_die()._run(()) == Right(42)


def test_zio_or_die_2() -> None:
    with pytest.raises(Bippy):
        ZIO.fail(Bippy()).or_die()._run(())


def test_environment_1() -> None:
    assert Environment[int]()._run(42) == Right(42)


def test_environment_2() -> None:
    assert Environment[int]().provide(42)._run(()) == Right(42)


def test_environment_3() -> None:
    assert Environment[int]().provide(42).provide("asdf")._run(()) == Right(42)


@pytest.mark.parametrize(
    "program,environment,expected_result",
    [
        (ZIO.succeed(42), None, Right(42)),
        (ZIO.fail(Bippy()), None, Left(Bippy)),
        (ZIO.effect(lambda: 42), None, Right(42)),
        (ZIO.effect(lambda: _raise(Bippy())), None, Left(Bippy)),  # type: ignore
        (ZIO.effect_catch(lambda: 42, Bippy), None, Right(42)),
        (ZIO.effect_catch(lambda: _raise(Bippy()), Bippy), None, Left(Bippy)),  # type: ignore
        (ZIO.effect_catch(lambda: _raise(Bippy()), NotBippy), None, Left(Bippy)),  # type: ignore
        (ZIO.succeed(42).catch(Bippy), None, Right(42)),
        (ZIO.access(len), "hello", Right(5)),
        (ZIO.access_m(lambda s: ZIO.succeed(len(s))), "hello", Right(5)),  # type: ignore
        (ZIO.access_m(lambda s: ZIO.fail(Bippy())), "hello", Left(Bippy)),  # type: ignore
        (ZIO.effect_total(lambda: 42), None, Right(42)),
        (ZIO.fail(Bippy()).catch(Bippy).either(), None, Right(Left(Bippy()))),
        (ZIO.succeed("Yay").catch(Bippy).either(), None, Right(Right("Yay"))),
        (ZIO.succeed(1).map(lambda x: x + 1).map(lambda x: x + 10), None, Right(12)),
        (ZIO.succeed(1).map(lambda x: x + 1).fail(Bippy()), None, Left(Bippy)),  # type: ignore
        (
            (
                ZIO.succeed(1)
                .flat_map(lambda x: ZIO.succeed(x + 1))
                .flat_map(lambda x: ZIO.succeed(x + 10))
            ),
            None,
            Right(12)
        ),
        (
            ZIO.succeed(1).flat_map(lambda x: ZIO.succeed(x + 1)).fail(Bippy()),  # type: ignore
            None,
            Left(Bippy)
        ),
        (ZIO.succeed(1) << ZIO.succeed(2), None, Right(2)),
        (ZIO.fail(Bippy()) << ZIO.succeed(2), None, Left(Bippy)),
        (ZIO.succeed(2) << ZIO.fail(Bippy()), None, Left(Bippy)),  # type: ignore
        (ZIO.succeed("a").zip(ZIO.succeed(42)), None, Right(("a", 42))),
        (ZIO.fail(Bippy()).zip(ZIO.succeed(42)), None, Left(Bippy)),
        (ZIO.succeed("a").zip(ZIO.fail(Bippy())), None, Left(Bippy)),
        (ZIO.succeed("a").either(), None, Right(Right("a"))),
        (ZIO.fail(Bippy()).either(), None, Right(Left(Bippy()))),
        (Environment[int](), 42, Right(42)),
        (Environment[int]().provide(42), None, Right(42)),
        (Environment[int]().provide(42).provide("asdf"), None, Right(42))
    ]
)
def test_unsafe_run(
    program: ZIO[R, E, A],
    environment: R,
    expected_result: Either[E, A]
) -> None:
    if isinstance(expected_result, Right):
        assert unsafe_run(program.provide(environment)) == expected_result.value
    elif isinstance(expected_result, Left):
        with pytest.raises(expected_result.value):
            unsafe_run(program.provide(environment))
    else:
        raise Exception("Impossible")


@pytest.mark.parametrize(
    "equivalence_relation",
    [
        eqr.EQ1,
        eqr.EQ2,
        eqr.EQ3,
        eqr.EQ4,
        eqr.EQ5,
        eqr.EQ6,
        eqr.EQ7,
    ]
)
def test_do_notation(equivalence_relation: eqr.Equiv[R, E, A]) -> None:
    output_p = unsafe_run(equivalence_relation.p.either().provide(equivalence_relation.environment))
    output_q = unsafe_run(equivalence_relation.q.either().provide(equivalence_relation.environment))
    assert output_p == output_q == equivalence_relation.expected_output


@pytest.mark.parametrize(
    "input",
    [
        Either.left(42),
        Either.right("hello")
    ]
)
def test_from_either(input: Either[int, str]) -> None:
    assert ZIO.from_either(input)._run(()) == input


@pytest.mark.parametrize(
    "input,expected",
    [
        (ZIO.fail("oh noes"), Right(Left("oh noes"))),
        (ZIO.succeed(42), Right(Right(42)))
    ]
)
def test_either(input: ZIO[object, str, int], expected: Either[str, int]) -> None:
    assert input.either()._run(()) == expected


@pytest.mark.parametrize(
    "input,expected",
    [
        (ZIO.succeed(Left("oh noes")), Left("oh noes")),
        (ZIO.succeed(Right(42)), Right(42))
    ]
)
def test_absolve(
    input: ZIO[object, NoReturn, Either[str, int]],
    expected: Either[str, int]
) -> None:
    assert input.absolve()._run(()) == expected


################################################################################
# Some classes for the match_type tests. I want to define them here so that the
# intent of the tests is clear (rather than scattering them to the winds of
# conftest.py).
################################################################################
@dataclass(frozen=True)
class X:
    x_value: int


@dataclass(frozen=True)
class Y:
    y_value: str


@dataclass(frozen=True)
class Z:
    z_value: Set[int]


case_x = Environment[X]().map(lambda x: [x.x_value])
case_y = Environment[Y]().map(lambda y: [y.y_value, y.y_value])
case_z = Environment[Z]().map(lambda z: [z.z_value, z.z_value, z.z_value])

id_x = Environment[X]()
id_y = Environment[Y]()
id_z = Environment[Z]()

in_x = X(42)
in_y = Y("a")
in_z = Z({42})

out_x = [42]
out_y = ["a", "a"]
out_z = [{42}, {42}, {42}]


@pytest.mark.parametrize(
    "input,expected",
    [
        (in_x, out_x),
        (in_y, in_y),
        (in_z, in_z),
    ]
)
def test_match_types_1(input: Union[X, Y, Z], expected: object) -> None:
    arrow = (
        Environment[object]()
        .match_types()
        .at_type(X, case_x)
        .at_type(Y, id_y)
        .at_type(Z, id_z)
    )
    assert unsafe_run(arrow.provide(input)) == expected


@pytest.mark.parametrize(
    "input,expected",
    [
        (in_x, in_x),
        (in_y, out_y),
        (in_z, in_z),
    ]
)
def test_match_types_2(input: Union[X, Y, Z], expected: object) -> None:
    arrow = (
        Environment[object]()
        .match_types()
        .at_type(X, id_x)
        .at_type(Y, case_y)
        .at_type(Z, id_z)
    )
    assert unsafe_run(arrow.provide(input)) == expected


@pytest.mark.parametrize(
    "input,expected",
    [
        (in_x, in_x),
        (in_y, in_y),
        (in_z, out_z),
    ]
)
def test_match_types_3(input: Union[X, Y, Z], expected: object) -> None:
    arrow = (
        Environment[object]()
        .match_types()
        .at_type(X, id_x)
        .at_type(Y, id_y)
        .at_type(Z, case_z)
    )
    assert unsafe_run(arrow.provide(input)) == expected


@pytest.mark.parametrize(
    "input,expected",
    [
        (in_x, out_x),
        (in_y, out_y),
        (in_z, out_z),
    ]
)
def test_match_types_4(input: Union[X, Y, Z], expected: object) -> None:
    arrow = (
        Environment[object]()
        .match_types()
        .at_type(X, case_x)
        .at_type(Y, case_y)
        .at_type(Z, case_z)
    )
    assert unsafe_run(arrow.provide(input)) == expected


def test_match_types_fall_through() -> None:
    with pytest.raises(TypeMatchException):
        arrow = (
            Environment[object]()
            .match_types()
            .at_type(X, case_x)
            .at_type(Y, case_y)
            .at_type(Z, case_z)
        )
        unsafe_run(arrow.provide("fall-through"))


def test_at_type_with_same_type_1() -> None:
    case_1 = Environment[str]().map(lambda s: s + "1")
    case_2 = Environment[str]().map(lambda s: s + "2")
    case_3 = Environment[str]().map(lambda s: s + "3")

    arrow = (
        Environment[str]()
        .match_types()
        .at_type(str, case_1)
        .at_type(str, case_2)
        .map(lambda s: s + "foo")
        .at_type(str, case_3)
    )

    assert unsafe_run(arrow.provide("")) == "1foo"


def test_at_type_with_same_type_2() -> None:
    case_1 = Environment[str]().map(lambda s: s + "1")
    case_2 = Environment[str]().map(lambda s: s + "2")
    case_3 = Environment[str]().map(lambda s: s + "3")

    arrow = (
        Environment[int]()
        .match_types()
        .at_type(str, case_1)
        .at_type(str, case_2)
        .at_type(str, case_3)
        .at_type(int, Environment[int]())
        .map(lambda x: str(x) + "!")
    )

    assert unsafe_run(arrow.provide(0)) == "0!"


def test_match_types_complex() -> None:
    case_1 = Environment[str]().map(lambda s: s + "1")
    case_2 = Environment[str]().map(lambda s: s + "2")
    case_3 = Environment[str]().map(lambda s: s + "3")

    with pytest.raises(TypeMatchException):
        unsafe_run(Environment[int]().match_types().provide(42))

    # Obviously grotesque use of `match_types`...but we should understand
    # its semantics.
    assert unsafe_run(
        Environment[str]()
        .match_types()
        .at_type(str, case_1)
        .at_type(str, case_2)
        .map(lambda s: s + "foo")
        .at_type(str, case_3)
        .provide("")
    ) == "1foo"

    with pytest.raises(TypeMatchException):
        unsafe_run(
            Environment[dict]()
            .match_types()
            .at_type(str, case_1)
            .at_type(str, case_2)
            .map(lambda s: s + "foo")
            .at_type(str, case_3)
            .provide({'ka': 'boom'})
        )

    with pytest.raises(TypeMatchException):
        unsafe_run(
            Environment[str]()
            .match_types()
            .provide("")
        )

    with pytest.raises(TypeMatchException):
        unsafe_run(
            Environment[str]()
            .match_types()
            .at_type(int, Environment[int]())
            .provide("")
        )

    assert unsafe_run(
        Environment[str]()
        .require(lambda s: len(s) > 5, lambda s: f"String '{s}' is too short.")
        .at_type(str, case_1)
        .either()
        .provide("foo")
    ) == Either.left("String 'foo' is too short.")


def test_asserting_1() -> None:
    assert unsafe_run(
        Environment[str]()
        .asserting(lambda s: s.startswith("h"), lambda s: FooException(s))
        .catch(FooException)
        .provide("hello")
    ) == "hello"


def test_asserting_2() -> None:
    assert unsafe_run(
        Environment[str]()
        .asserting(
            lambda s: s.startswith("x"),
            lambda s: FooException(f"Oh noes: {s}")
        )
        .catch(FooException)
        .either()
        .provide("hello")
    ) == Left(FooException("Oh noes: hello"))


def test_asserting_3() -> None:
    with pytest.raises(FooException) as exc:
        unsafe_run(
            Environment[str]()
            .asserting(
                lambda s: s.startswith("x"),
                lambda s: FooException(f"Oh noes: {s}")
            )
            .catch(BarException)
            .provide("hello")
        )
    assert str(exc.value) == "Oh noes: hello"


def test_asserting_4() -> None:
    assert unsafe_run(
        Environment[str]()
        .asserting(
            lambda s: s.startswith("x"),
            lambda s: FooException(f"{s} doesn't start with x")
        )
        .catch(BarException)
        .asserting(
            lambda s: s.endswith("x"),
            lambda s: BarException(f"{s} doesn't end with x")
        )
        .catch(FooException)
        .either()
        .provide("hello")
    ) == Left(FooException("hello doesn't start with x"))


@pytest.mark.parametrize(
    "input,expected",
    [
        (41, "Catch-all"),
        (42, "First arrow succeeded!"),
        (43, "Second arrow succeeded!"),
        (44, "Third arrow succeeded!"),
        (45, "Catch-all")
    ]
)
def test_or_else(input: int, expected: Either[int, str]) -> None:
    arrow_1 = (
        Environment[int]()
        .require(lambda x: x == 42, lambda x: f"Wrong guess: {x}. Expected 42.")
        .map(lambda _: "First arrow succeeded!")
    )
    arrow_2 = (
        Environment[int]()
        .require(lambda x: x == 43, lambda x: f"Wrong guess: {x}. Expected 43.")
        .map(lambda _: "Second arrow succeeded!")
    )
    arrow_3 = (
        Environment[int]()
        .require(lambda x: x == 44, lambda x: f"Wrong guess: {x}. Expected 43.")
        .map(lambda _: "Third arrow succeeded!")
    )
    arrow_4 = (
        Environment[int]()
        .map(lambda _: "Catch-all")
    )

    assert unsafe_run(
        arrow_1
        .or_else(arrow_2)
        .or_else(arrow_3)
        .or_else(arrow_4)
        .or_die()
        .provide(input)
    ) == expected


def test_swap_environments() -> None:
    program = (
        Environment[int]()
        .map(lambda x: Environment[str]().map(lambda s: f"Result is {x} {s}"))
        .swap_environments()
    )
    inner = unsafe_run(program.provide("hello"))
    result = unsafe_run(inner.provide(42))
    assert result == "Result is 42 hello"


def test_from_callable() -> None:
    def _f(arg_1: int, arg_2: str, *, arg_3: float) -> str:
        return f"{arg_1} {arg_2} {arg_3}"

    program = ZIO.from_callable(_f)
    assert unsafe_run(
        program.provide(FunctionArguments(42, "foo", arg_3=3.14))
    ) == "42 foo 3.14"


def test_to_callable() -> None:
    def _f(arg_1: int, arg_2: str, *, arg_3: float) -> str:
        return f"{arg_1} {arg_2} {arg_3}"

    g = ZIO.from_callable(_f).to_callable()
    assert g(42, "foo", arg_3=3.14) == "42 foo 3.14"


def test_from_to_callable_1() -> None:
    class Cat:
        def meow(self, *, volume: int) -> str:
            if volume < 10:
                return "meow"
            else:
                return "MEOW!"

    meow_to_callable = (
        Environment[Cat]()
        .map(lambda cat: ZIO.from_callable(cat.meow))
        .swap_environments()
        .to_callable()
    )

    assert unsafe_run(
        meow_to_callable(volume=11)
        .provide(Cat())
    ) == "MEOW!"


def test_from_to_callable_2() -> None:
    @dataclass(frozen=True)
    class SomeException(Exception):
        message: str

    class SomeAPI:
        def thing_that_may_fail(self, *, bippy: str) -> int:
            raise SomeException("Murphy's Law")

    safer_thing = (
        Environment[SomeAPI]()
        .map(
            lambda api: (
                ZIO.from_callable(api.thing_that_may_fail)
                .catch(SomeException)
                .either()
            )
        )
        .swap_environments()
        .to_callable()
    )

    assert unsafe_run(
        safer_thing(bippy="bippy")
        .provide(SomeAPI())
    ) == Left(SomeException("Murphy's Law"))
