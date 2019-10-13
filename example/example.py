"""A simple Python ZIO program that performs console IO.

For potentially better syntax using the macropy monad comprehension macro, see
`example.my_program.py` and `run_my_program.py`.
"""

from typing import NoReturn

from zio_py.console import Console, LiveConsole, read_line, print_line
from zio_py.runtime import Runtime
from zio_py.zio import ZIO, ZIOStatic


if __name__ == "__main__":
    program: ZIO[Console, Exception, None] = \
        print_line("Good morning!") \
        .flat_map(lambda _: read_line("What is your name? ")
        .flat_map(lambda name: print_line(f"Good to meet you, {name}!")))  # noqa


    runtime = Runtime[LiveConsole]()
    live_console = LiveConsole()

    result = runtime.unsafe_run_sync(program.provide(live_console))

    print(f"Result: {result}")
    print("The end!")
