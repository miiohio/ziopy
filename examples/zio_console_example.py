from typing import NoReturn, Union

import zio_py.services.console as console
import zio_py.services.system as system
from zio_py.environments import HasConsoleSystem
from zio_py.services.console import Console, LiveConsole
from zio_py.zio import ZIO, ZIOMonad, monadic, unsafe_run, Environment


@monadic
def program(
    do: ZIOMonad[Console, Union[EOFError, KeyboardInterrupt]]
) -> ZIO[
    Console,
    Union[EOFError, KeyboardInterrupt],
    str
]:
    con = do << Environment()

    do << con.print("Hello, what is your name?")
    name = do << con.input()
    do << con.print(f"Your name is: {name}")
    x = do << ZIO.succeed(1)

    while x < 20:
        x = do << (
            ZIO.succeed(x)
            .map(lambda p: p + 1)
            .flat_map(lambda q: ZIO.succeed(q - 1))
            .flat_map(lambda r: ZIO.succeed(r + 1))
        )

    do << con.print(f"The value of x is: {x}")
    return ZIO.succeed(f"Hello, {name}!")


p = program().provide(LiveConsole())
final_result = unsafe_run(p)
print(f"Final result (1) is: {final_result}")

# You can run the same program (value) over and over again.
final_result_2 = unsafe_run(p)
print(f"Final result (2) is: {final_result_2}")


@monadic
def prog(do: ZIOMonad[HasConsoleSystem, NoReturn]) -> ZIO[HasConsoleSystem, NoReturn, int]:
    age = do << console.get_input_from_console(
        prompt="How old are you?\n",
        parse_value=ZIO.from_callable(str).map(int).catch(ValueError).either().to_callable(),
        default_value=21
    )
    do << console.print(f"You are {age} years old.")
    return ZIO.succeed(age)


unsafe_run(prog().provide({'console': LiveConsole(), 'system': system.LiveSystem()}))
