from typing import List

import pytest

from zio_py.runtime import Runtime
from zio_py.syntax import macros, monadic  # noqa: F401
from zio_py.zio import UIO, ZIOStatic


def test_no_binds_1():
    @monadic
    def func() -> int:
        return 42

    assert func() == 42


def test_no_binds_2():
    @monadic
    def func() -> int:
        return 100 if 11 > 22 else 42

    assert func() == 42


def test_no_binds_3():
    @monadic
    def func() -> UIO[int]:
        return ZIOStatic.succeed(42)

    assert func() == ZIOStatic.succeed(42)


def test_simple_binds_1(simple_runtime: Runtime):
    @monadic
    def func() -> UIO[int]:
        x = ~ZIOStatic.succeed(42)
        return ZIOStatic.succeed(x)

    assert simple_runtime.unsafe_run_sync(func()) == 42


def test_simple_binds_2(simple_runtime: Runtime):
    @monadic
    def func() -> UIO[int]:
        x = ~ZIOStatic.succeed(1)
        y = ~ZIOStatic.succeed(2)
        z = ~ZIOStatic.succeed(3)
        return ZIOStatic.succeed(x + y + z)

    assert simple_runtime.unsafe_run_sync(func()) == 6


def test_simple_binds_3(simple_runtime: Runtime):
    @monadic
    def func() -> UIO[int]:
        x = ~ZIOStatic.succeed(1)
        y = ~ZIOStatic.succeed(2)
        z = ~ZIOStatic.succeed(3)
        sum = x + y + z
        return ZIOStatic.succeed(sum)

    assert simple_runtime.unsafe_run_sync(func()) == 6


def test_simple_binds_4(simple_runtime: Runtime):
    @monadic
    def func() -> UIO[int]:
        x = 1
        y = ~ZIOStatic.succeed(2)
        z = 3
        sum = ZIOStatic.succeed(x + y + z)
        return sum

    assert simple_runtime.unsafe_run_sync(func()) == 6


def test_simple_binds_5(simple_runtime: Runtime):
    @monadic
    def func() -> UIO[int]:
        x, y, z = ~ZIOStatic.succeed([1, 2, 3])
        return ZIOStatic.succeed(x + y + z)

    assert simple_runtime.unsafe_run_sync(func()) == 6


def test_simple_binds_6(simple_runtime: Runtime):
    @monadic
    def func() -> UIO[int]:
        x, *rest = ~ZIOStatic.succeed([1, 2, 3])
        return ZIOStatic.succeed(x + sum(rest))

    assert simple_runtime.unsafe_run_sync(func()) == 6


def test_simple_binds_7(simple_runtime: Runtime):
    @monadic
    def func(xs: List[int]) -> UIO[int]:
        x, *rest = ~ZIOStatic.succeed(xs)
        return ZIOStatic.succeed(x + sum(rest))

    assert simple_runtime.unsafe_run_sync(func([1, 2, 3])) == 6


def test_simple_binds_8(simple_runtime: Runtime):
    @monadic
    def func(xs: UIO[List[int]]) -> UIO[int]:
        x, *rest = ~xs
        return ZIOStatic.succeed(x + sum(rest))

    assert simple_runtime.unsafe_run_sync(func(ZIOStatic.succeed([1, 2, 3]))) == 6


def test_nested_binds_1(simple_runtime: Runtime):
    @monadic
    def func() -> UIO[int]:
        @monadic
        def get_numbers() -> UIO[List[int]]:
            xs = ~ZIOStatic.succeed([1, 2, 3])
            return ZIOStatic.succeed(xs)

        x, *rest = ~get_numbers()
        return ZIOStatic.succeed(x + sum(rest))

    assert simple_runtime.unsafe_run_sync(func()) == 6


def test_throwaway_binds_1(simple_runtime: Runtime):
    xs: List[int] = []

    def impure() -> None:
        nonlocal xs
        xs.append(1)

    @monadic
    def func() -> UIO[None]:
        ~ZIOStatic.effect_total(impure)
        ~ZIOStatic.effect_total(impure)
        ~ZIOStatic.effect_total(impure)
        return ZIOStatic.succeed(None)

    simple_runtime.unsafe_run_sync(func())
    assert xs == [1, 1, 1]


def test_throwaway_binds_2(simple_runtime: Runtime):
    xs: List[int] = []

    def impure() -> None:
        nonlocal xs
        xs.append(1)

    @monadic
    def func() -> UIO[None]:
        nonlocal xs
        ~ZIOStatic.effect_total(impure)
        xs.append(2)
        ~ZIOStatic.effect_total(impure)
        xs.append(3)
        ~ZIOStatic.effect_total(impure)
        xs.append(4)
        return ZIOStatic.succeed(None)

    simple_runtime.unsafe_run_sync(func())
    assert xs == [1, 2, 1, 3, 1, 4]


def test_if_then_else_1(simple_runtime: Runtime):
    @monadic
    def func() -> UIO[str]:
        x = ~ZIOStatic.succeed(False)
        if x:
            return ZIOStatic.succeed("True")
        else:
            return ZIOStatic.succeed("False")

    assert simple_runtime.unsafe_run_sync(func()) == "False"


def test_if_then_else_2(simple_runtime: Runtime):
    @monadic
    def func() -> UIO[int]:
        x = ~ZIOStatic.succeed(False)
        if x:
            a, b, c = ~ZIOStatic.succeed([1, 2, 3])
        else:
            a, b, c = ~ZIOStatic.succeed([4, 5, 6])
        return ZIOStatic.succeed(a + b + c)

    assert simple_runtime.unsafe_run_sync(func()) == 4 + 5 + 6


def test_if_then_else_3(simple_runtime: Runtime):
    xs: List[int] = []

    def impure_1() -> None:
        nonlocal xs
        xs.append(1)

    def impure_2() -> None:
        nonlocal xs
        xs.append(2)

    @monadic
    def func() -> UIO[int]:
        x = ~ZIOStatic.succeed(False)
        if x:
            ~ZIOStatic.effect_total(impure_1)
        else:
            ~ZIOStatic.effect_total(impure_2)
        return ZIOStatic.succeed(42)

    result = simple_runtime.unsafe_run_sync(func())
    print(result)
    assert simple_runtime.unsafe_run_sync(func()) == 42


@pytest.mark.parametrize(
    "x1, x2, expected", [
        (True, True, 'A'),
        (True, False, 'B'),
        (False, True, 'C'),
        (False, False, 'D')
    ]
)
def test_if_then_else_nested(simple_runtime: Runtime, x1: bool, x2: bool, expected: str):
    @monadic
    def func() -> UIO[str]:
        x = ~ZIOStatic.succeed(x1)
        if x:
            bippy = ~ZIOStatic.succeed(x2)
            if bippy:
                return ZIOStatic.succeed('A')
            return ZIOStatic.succeed('B')
        else:
            bippy = ~ZIOStatic.succeed(x2)
            if bippy:
                return ZIOStatic.succeed('C')
            else:
                return ZIOStatic.succeed('D')

    assert simple_runtime.unsafe_run_sync(func()) == expected


def test_recursion(simple_runtime: Runtime):
    @monadic
    def factorial(n: int) -> UIO[int]:
        if n == 0:
            return ZIOStatic.succeed(1)
        else:
            m = ~factorial(n - 1)
            return ZIOStatic.succeed(n * m)

    assert simple_runtime.unsafe_run_sync(factorial(1)) == 1
    assert simple_runtime.unsafe_run_sync(factorial(2)) == 2
    assert simple_runtime.unsafe_run_sync(factorial(3)) == 6
    assert simple_runtime.unsafe_run_sync(factorial(4)) == 24

# def test_try_1(simple_runtime: Runtime):
#     @monadic
#     def func() -> UIO[int]:
#         try:
#             x = ~ZIOStatic.succeed(42)
#             return ZIOStatic.succeed(x)
#         except:
#             return ZIOStatic.succeed(100)

#     assert simple_runtime.unsafe_run_sync(func()) == 42

# # TODO: Error handling
# def test_try_2(simple_runtime: Runtime):
#     @monadic
#     def func() -> UIO[int]:
#         try:
#             x = ~ZIOStatic.succeed(42)
#             raise ValueError
#             return ZIOStatic.succeed(x)
#         except ValueError:
#             return ZIOStatic.succeed(100)

#     assert simple_runtime.unsafe_run_sync(func()) == 42

# def test_complex_1(simple_runtime: Runtime):
#     A = TypeVar('A')
#     @monadic
#     def get_input_from_console_pure(
#             prompt: str,
#             value_mapper: Callable[[str],ZIO[Any, ValueError, A]],
#             is_valid_value: Callable[[A], bool],
#             default_value: Optional[A]) -> ZIO[Console, Exception, A]:
#         response = None
#         while response is None or not is_valid_value(response):
#             try:
#                 value = ~read_line(prompt)
#                 if value == '' and default_value is not None:
#                     return ZIOStatic.succeed(default_value)
#                 response = value_mapper(value)
#             except (EOFError, KeyboardInterrupt):
#                 print("")
#                 sys.exit(0)
#             except ValueError:
#                 response = None
#         return response
