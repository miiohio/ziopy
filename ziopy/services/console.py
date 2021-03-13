import builtins
from abc import ABCMeta, abstractmethod
from typing import Callable, List, NoReturn, Optional, TypeVar, Union

import ziopy.services.mock_effects.console as console_effect
from ziopy.either import Either, Right
from ziopy.zio import ZIO, Environment, ZIOMonad, monadic
from ziopy.services.system import System, HasSystem
from typing_extensions import Literal, Protocol

A = TypeVar('A')
E = TypeVar('E')


class Console(metaclass=ABCMeta):
    @abstractmethod
    def print(self, line: str) -> ZIO[object, NoReturn, None]:
        pass  # pragma: nocover

    @abstractmethod
    def input(
        self,
        prompt: Optional[str] = None
    ) -> ZIO[object, Union[EOFError, KeyboardInterrupt], str]:
        pass  # pragma: nocover

    @monadic
    def get_input_from_console(
        self,
        prompt: str,
        parse_value: Callable[[str], Either[E, A]],
        default_value: Optional[A],
        do: ZIOMonad[System, NoReturn]
    ) -> ZIO[System, NoReturn, A]:
        while True:
            keyboard_input = do << (
                self.input(prompt)
                .either()
                .map(lambda e: e.to_union())
            )

            if isinstance(keyboard_input, (EOFError, KeyboardInterrupt)):
                do << self.print("")
                system = do << Environment()
                return system.exit()

            if keyboard_input == '' and default_value is not None:
                return ZIO.succeed(default_value)

            parse_result = parse_value(keyboard_input)
            if isinstance(parse_result, Right):
                return ZIO.succeed(parse_result.value)

    @monadic
    def ask(
        self,
        prompt: str,
        default: Literal['y', 'n'],
        do: ZIOMonad[System, NoReturn]
    ) -> ZIO[System, NoReturn, bool]:
        default_str = 'Y/n' if default == 'y' else 'y/N'
        choice = do << self.get_input_from_console(
            prompt=f"{prompt} [{default_str}]: ",
            parse_value=(
                ZIO.from_callable(str)
                .map(str.lower)
                .require(lambda s: s in {'y', 'n'}, lambda s: s)
                .either()
                .to_callable()
            ),
            default_value=default
        )
        return ZIO.succeed(choice == 'y')


class LiveConsole(Console):
    def print(self, line: str) -> ZIO[object, NoReturn, None]:
        return ZIO.effect_total(lambda: builtins.print(line))

    def input(
        self,
        prompt: Optional[str] = None
    ) -> ZIO[object, Union[EOFError, KeyboardInterrupt], str]:
        return (
            ZIO.effect_catch(
                lambda: builtins.input(prompt) if prompt is not None else builtins.input(),
                EOFError
            )
            .catch(KeyboardInterrupt)
        )


class MockConsole(Console):
    def __init__(self, user_input: List[Union[EOFError, KeyboardInterrupt, str]] = None) -> None:
        self._effects: List[Union[console_effect.Print, console_effect.Input]] = []
        if user_input is None:
            user_input = []
        self._user_input = user_input

    def print(self, line: str) -> ZIO[object, NoReturn, None]:
        self._effects.append(console_effect.Print(line))
        return ZIO.succeed(None)

    def input(
        self,
        prompt: Optional[str] = None
    ) -> ZIO[object, Union[EOFError, KeyboardInterrupt], str]:
        user_input = self._user_input.pop(0)
        self._effects.append(console_effect.Input(prompt, user_input))
        if isinstance(user_input, str):
            return ZIO.succeed(user_input)
        else:
            result: Union[EOFError, KeyboardInterrupt] = user_input
            return ZIO.fail(result)

    @property
    def effects(self) -> List[Union[console_effect.Print, console_effect.Input]]:
        return self._effects

    @property
    def user_input(self) -> List[Union[EOFError, KeyboardInterrupt, str]]:
        return self._user_input


class HasConsole(Protocol):
    @property
    def console(self) -> Console:
        pass  # pragma: nocover


print = (
    Environment[HasConsole]()
    .map(lambda env: ZIO.from_callable(env.console.print).flatten())
    .swap_environments()
    .to_callable()
)

input = (
    Environment[HasConsole]()
    .map(lambda env: ZIO.from_callable(env.console.input).flatten())
    .swap_environments()
    .to_callable()
)


class HasConsoleSystem(HasConsole, HasSystem, Protocol):
    pass


def get_input_from_console(
    prompt: str,
    parse_value: Callable[[str], Either[E, A]],
    default_value: Optional[A]
) -> ZIO[HasConsoleSystem, NoReturn, A]:
    return (
        Environment[HasConsoleSystem]()
        .flat_map(
            lambda env: env.console.get_input_from_console(
                prompt, parse_value, default_value
            ).provide(env.system)
        )
    )


def ask(prompt: str, default: Literal['y', 'n']) -> ZIO[HasConsoleSystem, NoReturn, bool]:
    return Environment[HasConsoleSystem]().flat_map(
        lambda env: env.console.ask(prompt, default).provide(env.system)
    )
