from typing import Callable, NoReturn, Type, TypeVar, Union

import pytest

from zio_py.either import Any, Either, EitherException, Left, Right

A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')
X = TypeVar('X', bound=Exception)


@pytest.mark.parametrize(
    "input,expected",
    [
        (42, Left(42)),
        ("asdf", Left("asdf")),
    ]
)
def test_either_left(input: Either[A, NoReturn], expected: Left[A]) -> None:
    x = Either.left(input)
    assert x == x.to_left() == expected

    with pytest.raises(TypeError):
        x.to_right()  # type: ignore


@pytest.mark.parametrize(
    "input,expected",
    [
        (42, Right(42)),
        ("asdf", Right("asdf")),
    ]
)
def test_either_right(input: Either[A, NoReturn], expected: Right[A]) -> None:
    x = Either.right(input)
    assert x == x.to_right() == expected

    with pytest.raises(TypeError):
        x.to_left()  # type: ignore


@pytest.mark.parametrize(
    "value,left_type,right_type",
    [
        (42, int, str),
        ("asdf", str, int)
    ]
)
def test_from_union_left(value: Union[A, B], left_type: Type[A], right_type: Type[B]) -> None:
    assert Either.from_union(value, left_type, right_type) == Either.left(value)


@pytest.mark.parametrize(
    "value,left_type,right_type",
    [
        (42, int, str),
        ("asdf", str, int)
    ]
)
def test_from_union_right(value: Union[A, B], left_type: Type[A], right_type: Type[B]) -> None:
    assert Either.from_union(value, right_type, left_type) == Either.right(value)


def test_from_union_fails() -> None:
    with pytest.raises(TypeError):
        Either.from_union([1, 2, 3], int, str)  # type: ignore


def test_match_left() -> None:
    x: Either[int, str] = Either.left(42)
    assert x.match(lambda x: x.value + 1, lambda y: y.value + "!") == 43


def test_match_right() -> None:
    x = Either.right("hello")
    assert x.match(lambda x: x.value + 1, lambda y: y.value + "!") == "hello!"


def test_match_fails() -> None:
    # Don't even *think* about making a subclass of Either! :-)
    class OhNoYouDidnt(Either[int, str]):
        pass

    with pytest.raises(TypeError):
        OhNoYouDidnt().match(lambda x: x, lambda x: x)


def test_fold_left() -> None:
    x: Either[int, str] = Either.left(42)
    assert x.fold(lambda x: x + 1, lambda y: y + "!") == 43


def test_fold_right() -> None:
    x = Either.right("hello")
    assert x.fold(lambda x: x + 1, lambda y: y + "!") == "hello!"


@pytest.mark.parametrize(
    "input,left_type,right_type",
    [
        (42, int, str),
        (42, str, int),
        ("asdf", str, int),
        ("asdf", int, str),
    ]
)
def test_swap_left(input: A, left_type: Type[A], right_type: Type[B]) -> None:
    x: Either[A, B] = Either.left(input)
    assert x.swap().swap() == x == Either.right(input).swap()


@pytest.mark.parametrize(
    "input,left_type,right_type",
    [
        (42, int, str),
        (42, str, int),
        ("asdf", str, int),
        ("asdf", int, str),
    ]
)
def test_swap_right(input: B, left_type: Type[A], right_type: Type[B]) -> None:
    x: Either[A, B] = Either.right(input)
    assert x.swap().swap() == x == Either.left(input).swap()


@pytest.mark.parametrize(
    "input,f,expected",
    [
        (Left(42), lambda x: x + 1, Left(42)),
        (Right(42), lambda x: [x + 1], Right([43])),
        (Left("hello"), lambda x: x + "!", Left("hello")),
        (Right("hello"), lambda x: [x + "!"], Right(["hello!"]))
    ]
)
def test_map(input: Either[A, B], f: Callable[[B], C], expected: Either[A, B]) -> None:
    assert input.map(f) == expected


@pytest.mark.parametrize(
    "input,f,expected",
    [
        (Right(42), lambda x: x + 1, Right(42)),
        (Left(42), lambda x: [x + 1], Left([43])),
        (Right("hello"), lambda x: x + "!", Right("hello")),
        (Left("hello"), lambda x: [x + "!"], Left(["hello!"]))
    ]
)
def test_map_left(input: Either[A, B], f: Callable[[A], C], expected: Either[A, B]) -> None:
    assert input.map_left(f) == expected


@pytest.mark.parametrize(
    "input,f,expected",
    [
        (Left(42), lambda x: Left(x + 1), Left(42)),
        (Left(42), lambda x: Right(x + 1), Left(42)),
        (Right(42), lambda x: Left([x + 1]), Left([43])),
        (Right(42), lambda x: Right([x + 1]), Right([43])),
        (Left("hello"), lambda x: Left(x + "!"), Left("hello")),
        (Left("hello"), lambda x: Right(x + "!"), Left("hello")),
        (Right("hello"), lambda x: Left([x + "!"]), Left(["hello!"])),
        (Right("hello"), lambda x: Right([x + "!"]), Right(["hello!"]))
    ]
)
def test_flat_map(
    input: Either[A, B],
    f: Callable[[B], Either[A, C]],
    expected: Either[A, B]
) -> None:
    assert input.flat_map(f) == expected


def test_flatten_left() -> None:
    x: Either[str, Either[str, int]] = Either.left("asdf")
    assert x.flatten() == Left("asdf")


def test_flatten_right() -> None:
    x: Either[str, Either[str, int]] = Either.right(Either.right(42))
    assert x.flatten() == Right(42)


@pytest.mark.parametrize(
    "input,f,expected",
    [
        (Left(42), lambda x: Left(x + 1), Left(42)),
        (Left(42), lambda x: Right(x + 1), Left(42)),
        (Right(42), lambda x: Left([x + 1]), Left([43])),
        (Right(42), lambda x: Right([x + 1]), Right([43])),
        (Left("hello"), lambda x: Left(x + "!"), Left("hello")),
        (Left("hello"), lambda x: Right(x + "!"), Left("hello")),
        (Right("hello"), lambda x: Left([x + "!"]), Left(["hello!"])),
        (Right("hello"), lambda x: Right([x + "!"]), Right(["hello!"]))
    ]
)
def test_flatten_is_flat_map(
    input: Either[A, B],
    f: Callable[[B], Either[A, C]],
    expected: Either[A, B]
) -> None:
    assert input.flat_map(f) == input.map(f).flatten() == expected


@pytest.mark.parametrize(
    "input,predicate,to_error,expected",
    [
        (Left(42), lambda x: x > 0, lambda x: f"fail{x}", Left(42)),
        (Left(42), lambda x: x < 0, lambda x: f"fail{x}", Left(42)),
        (Right(42), lambda x: x > 0, lambda x: f"fail{x}", Right(42)),
        (Right(42), lambda x: x < 0, lambda x: f"fail{x}", Left("fail42")),
    ]
)
def test_require_right(
    input: Either[A, B],
    predicate: Callable[[B], bool],
    to_error: Callable[[B], C],
    expected: Either[Union[A, C], B]
) -> None:
    assert input.require(predicate, to_error) == expected


class BippyException(Exception):
    pass


@pytest.mark.parametrize(
    "input,predicate,to_error,expected",
    [
        (Left(42), lambda x: x > 0, lambda x: BippyException(f"fail{x}"), Left(42)),
        (Left(42), lambda x: x < 0, lambda x: BippyException(f"fail{x}"), Left(42)),
        (Right(42), lambda x: x > 0, lambda x: BippyException(f"fail{x}"), Right(42))
    ]
)
def test_asserting_no_exception(
    input: Either[A, B],
    predicate: Callable[[B], bool],
    to_error: Callable[[B], X],
    expected: Either[Union[A, X], B]
) -> None:
    assert input.asserting(predicate, to_error) == expected


@pytest.mark.parametrize(
    "input,predicate,to_error,exception_type,exception_text",
    [
        (Right(42), lambda x: x < 0, lambda x: BippyException(f"fail{x}"), BippyException, "fail42")
    ]
)
def test_asserting_exception(
    input: Either[A, B],
    predicate: Callable[[B], bool],
    to_error: Callable[[B], X],
    exception_type: Type[X],
    exception_text: str
) -> None:
    with pytest.raises(exception_type) as exc:
        input.asserting(predicate, to_error)
    assert str(exc.value) == exception_text


def test_raise_errors_regular_value() -> None:
    with pytest.raises(EitherException) as exc:
        Either.left(42).raise_errors()
    assert exc.value == EitherException(value=42)


def test_raise_errors_no_errors() -> None:
    assert Either.right("hello").raise_errors() == Right("hello")


def test_raise_errors_exception_on_left() -> None:
    with pytest.raises(BippyException) as exc:
        Either.left(BippyException("Oh noes!")).raise_errors()
    assert str(exc.value) == "Oh noes!"


def test_raise_errors_left_flat_map() -> None:
    with pytest.raises(BippyException) as exc:
        (
            Either.left(BippyException("Oh noes!"))
            .flat_map(lambda _: Either.right(42))
            .raise_errors()
        )
    assert str(exc.value) == "Oh noes!"


def test_raise_errors_right_flat_map() -> None:
    with pytest.raises(BippyException) as exc:
        (
            Either.right(42)
            .flat_map(lambda _: Either.left(BippyException("Oh noes!")))
            .raise_errors()
        )
    assert str(exc.value) == "Oh noes!"


def test_raise_errors_at_end_gets_first_exception() -> None:
    with pytest.raises(BippyException) as exc:
        (
            Either.right(42)
            .flat_map(lambda _: Either.left(BippyException("kaboom 1")))
            .flat_map(lambda _: Either.left(BippyException("kaboom 2")))
            .flat_map(lambda _: Either.left(BippyException("kaboom 3")))
            .raise_errors()
        )
    assert str(exc.value) == "kaboom 1"


def test_multiple_raise_errors() -> None:
    with pytest.raises(BippyException) as exc:
        (
            Either.right(42)
            .raise_errors()
            .flat_map(lambda _: Either.left(BippyException("kaboom 1")))
            .flat_map(lambda _: Either.left(BippyException("kaboom 2")))
            .flat_map(lambda _: Either.left(BippyException("kaboom 3")))
            .raise_errors()
        )
    assert str(exc.value) == "kaboom 1"


def test_tap() -> None:
    x = 0

    def foo(arg: Either[int, str]) -> None:
        nonlocal x
        x = arg.map(len).fold(lambda x: x, lambda x: x)

    e: Either[int, str] = Either.left(42)
    assert e.tap(foo) == e
    assert x == 42

    e = Either.right("hello")
    assert e.tap(foo) == e
    assert x == len("hello")


def test_display(capsys: Any) -> None:
    e: Either[int, str] = Either.left(42)
    assert e.display() == e
    captured = capsys.readouterr()
    assert captured.out == str(e) + "\n"
    assert e.display("Bippy") == e
    captured = capsys.readouterr()
    assert captured.out == "Bippy:\n" + str(e) + "\n"

    e = Either.right("hello")
    assert e.display() == e
    captured = capsys.readouterr()
    assert captured.out == str(e) + "\n"
    assert e.display("Bippy") == e
    captured = capsys.readouterr()
    assert captured.out == "Bippy:\n" + str(e) + "\n"


def test_to_union() -> None:
    # The point of this test is to ensure that mypy's type inference works
    # properly, ergo we prefer to not parametrize it.

    def foo(x: Union[int, str]) -> bool:
        return isinstance(x, int) or isinstance(x, str)

    e: Either[int, str] = Left(42)
    assert e.to_union() == 42
    assert foo(e.to_union())

    e = Right("hello")
    assert e.to_union() == "hello"
    assert foo(e.to_union())

    # mypy should properly unify Union[NoReturn, X] for all types X.
    assert Either.left(42).to_union() + 1 == 43
    assert len(Either.right("hello").to_union()) == len("hello")
