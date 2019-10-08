from typing import NoReturn

from zio.console import Console, LiveConsole
from zio.runtime import Runtime
from zio.zio import ZIO, ZIOStatic

def print_line(line: str) -> ZIO[Console, NoReturn, None]:
    return ZIOStatic.access_m(lambda env: env.print(line))

def read_line(prompt: str) -> ZIO[Console, Exception, str]:
    return ZIOStatic.access_m(lambda env: env.input(prompt))

program: ZIO[Console, Exception, None] = \
    print_line("Good morning!") \
        .flat_map(lambda _: read_line("What is your name? ") \
        .flat_map(lambda name: print_line(f"Good to meet you, {name}!")))

runtime = Runtime[LiveConsole]()
live_console = LiveConsole()

result = runtime.unsafe_run_sync(program.provide(live_console))

print(f"Result: {result}")
print("The end!")
