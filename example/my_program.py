""" A ZIO program written using macropy-enabled syntax for monadic binds.

We abuse the Python invert `~` unary operator to tell the macro which terms
should be transformed into appropriate calls to `flat_map` and `map`.

This is inspired by Scala's for comprehension desugaring.
See:  https://docs.scala-lang.org/tutorials/FAQ/yield.html
"""

from zio_py.console import Console, print_line, read_line
from zio_py.syntax import macros, monadic  # noqa: F401
from zio_py.zio import ZIO, ZIOStatic


# To use the `~` short-hand syntax for monadic binds within a function,
# decorate your function with the `@monadic` decorator.
@monadic
def my_program() -> ZIO[Console, Exception, int]:
    # You can declare variables that are not lifted into a monadic context.
    w = 'sunshine'

    # This is a monadic bind where we bind to a throwaway variable.
    # Desugars to `print_line(...).flat_map(...)`
    ~print_line(f'Good morning {w}!')

    # You *can* include effectful lines.  That's fine.
    print("It's a fantastic day to write ZIO programs in Python.")

    # This is a monadic bind where the variable is called `name`.
    # Desugars (approximately) to `read_line(...).flat_map(lambda name: ...)`
    name = ~read_line("Enter your name: ")

    # Yes, type inference with mypy and in the IDE works!
    # reveal_type(name) will show `str`

    your_age = ~read_line("Enter your age: ").map(int)
    ~print_line(f"Good to meet you, {name}!")
    ~print_line(f"Your age is {your_age}.")

    # if/then/else logic works as you'd expect
    if your_age >= 21:
        ~print_line("You are 21 or older")
        age_of_majority = True
    else:
        ~print_line("You are younger than 21")
        age_of_majority = False
    ~print_line("You're an adult" if age_of_majority
                else "You're young, lucky you")

    # The usual complex assignment syntaxes work as well.
    [x, y, z] = ~ZIOStatic.succeed([1, 2, 3])
    ~print_line(f"X is {x}")
    ~print_line(f"Y is {y}")
    ~print_line(f"Z is {z}")

    # The `ZIOStatic.succeed(1000)` is like `return 1000` in Haskell, or
    # `yield 1000` in Scala.
    # The rule is simple; you just have to return a value consistent with the
    # type signature of your function (like always).  Mypy will complain
    # at you if you get anything wrong.
    return ZIOStatic.succeed(1000)
