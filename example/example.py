"""A simple Python ZIO program that performs console IO.

For potentially better syntax using the macropy monad comprehension macro, see
`example.my_program.py` and `run_my_program.py`.
"""

from typing import NoReturn

from zio.console import Console, LiveConsole
from zio.runtime import Runtime
from zio.zio import ZIO, ZIOStatic


def print_line(line: str) -> ZIO[Console, NoReturn, None]:
    return ZIOStatic.access_m(lambda env: env.print(line))


def read_line(prompt: str) -> ZIO[Console, Exception, str]:
    return ZIOStatic.access_m(lambda env: env.input(prompt))


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
