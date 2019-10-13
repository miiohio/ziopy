""" A ZIO program written using macropy-enabled syntax for monadic binds.

We abuse the Python invert `~` unary operator to tell the macro which terms
should be transformed into appropriate calls to `flat_map` and `map`.

This is inspired by Scala's for comprehension desugaring.
See:  https://docs.scala-lang.org/tutorials/FAQ/yield.html
"""

from typing import Any

from zio_py.zio import ZIO, ZIOStatic
from zio_py.console import Console, print_line, read_line
from zio_py.syntax import macros, monad

# To keep the IDE happy, declare `program` here.  Technically this
# is not necessary, as it is instantiated/bound via the `with monad`
# block below.
program: ZIO[Console, Exception, int]

with monad(program):
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
    your_age = 42
    ~print_line(f"Good to meet you, {name}!")
    ~print_line(f"Your age is {your_age}.")

    # The `~ZIOStatic.succeed(1000)` is like `return 1000` in Haskell, or
    # `yield 1000` in Scala.
    print("That's all folks.")
    ~ZIOStatic.succeed(1000)
