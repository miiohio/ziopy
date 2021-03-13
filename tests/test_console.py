from typing import List, Union
from typing_extensions import Literal

import pytest
from unittest.mock import patch

import ziopy.services.console as console
import ziopy.services.mock_effects.console as console_effect
import ziopy.services.mock_effects.system as system_effect
from ziopy.environments import ConsoleEnvironment, ConsoleSystemEnvironment
from ziopy.zio import ZIO, unsafe_run
from ziopy.services.console import LiveConsole, MockConsole
from ziopy.services.system import MockSystem


def test_live_console_print_without_running() -> None:
    with patch('builtins.print') as mock_print:
        console.print("Hello world").provide(ConsoleEnvironment(LiveConsole()))
    mock_print.assert_not_called()


def test_live_console_print_with_running() -> None:
    with patch('builtins.print', return_value=None) as mock_print:
        program = console.print("Hello world").provide(ConsoleEnvironment(LiveConsole()))
        output = unsafe_run(program)
        assert output is None
    mock_print.assert_called_with("Hello world")


def test_live_console_input_no_prompt_without_running() -> None:
    with patch('builtins.input') as mock_input:
        console.input().provide(ConsoleEnvironment(LiveConsole()))
    mock_input.assert_not_called()


def test_live_console_input_no_prompt_with_running() -> None:
    with patch('builtins.input', return_value="Hello") as mock_input:
        program = console.input().provide(ConsoleEnvironment(LiveConsole()))
        output = unsafe_run(program)

    assert output == "Hello"
    mock_input.assert_called_with()


def test_live_console_input_with_prompt() -> None:
    with patch('builtins.input', return_value="Hello") as mock_input:
        program = console.input("Prompt").provide(ConsoleEnvironment(LiveConsole()))
        output = unsafe_run(program)

    assert output == "Hello"
    mock_input.assert_called_with("Prompt")


def test_live_console_input_with_eof_error() -> None:
    with patch('builtins.input', side_effect=EOFError) as mock_input:
        program = console.input("Prompt").provide(ConsoleEnvironment(LiveConsole()))

        with pytest.raises(EOFError):
            unsafe_run(program)
    mock_input.assert_called_with("Prompt")


def test_live_console_input_with_keyboard_interrupt() -> None:
    with patch('builtins.input', side_effect=KeyboardInterrupt) as mock_input:
        program = console.input("Prompt").provide(ConsoleEnvironment(LiveConsole()))

        with pytest.raises(KeyboardInterrupt):
            unsafe_run(program)
    mock_input.assert_called_with("Prompt")


def test_mock_console_print() -> None:
    mock_console = MockConsole()
    output = unsafe_run(
        (console.print("Hello") << console.print("World")).provide(ConsoleEnvironment(mock_console))
    )
    assert output is None

    assert mock_console.effects == [
        console_effect.Print("Hello"),
        console_effect.Print("World")
    ]


def test_get_input_from_console_1() -> None:
    program = console.get_input_from_console(
        prompt="How much wood would a woodchuck chuck?",
        parse_value=ZIO.from_callable(str).map(int).catch(ValueError).either().to_callable(),
        default_value=None
    )

    mock_console = MockConsole(["42"])
    mock_system = MockSystem()

    output = unsafe_run(
        program.provide(
            ConsoleSystemEnvironment(console=mock_console, system=mock_system)
        )
    )
    assert output == 42
    assert mock_console.effects == [
        console_effect.Input("How much wood would a woodchuck chuck?", "42")
    ]
    assert mock_console.user_input == []


def test_get_input_from_console_2() -> None:
    program = console.get_input_from_console(
        prompt="How much wood would a woodchuck chuck?",
        parse_value=ZIO.from_callable(str).map(int).catch(ValueError).either().to_callable(),
        default_value=None
    )

    mock_console = MockConsole(["bad", "input", "42"])
    mock_system = MockSystem()

    output = unsafe_run(
        program.provide(
            ConsoleSystemEnvironment(console=mock_console, system=mock_system)
        )
    )
    assert output == 42
    assert mock_console.effects == [
        console_effect.Input("How much wood would a woodchuck chuck?", "bad"),
        console_effect.Input("How much wood would a woodchuck chuck?", "input"),
        console_effect.Input("How much wood would a woodchuck chuck?", "42")
    ]
    assert mock_console.user_input == []


def test_get_input_from_console_default() -> None:
    program = console.get_input_from_console(
        prompt="How much wood would a woodchuck chuck?",
        parse_value=ZIO.from_callable(str).map(int).catch(ValueError).either().to_callable(),
        default_value=42
    )

    mock_console = MockConsole(["bad", "input", ""])
    mock_system = MockSystem()
    output = unsafe_run(
        program.provide(
            ConsoleSystemEnvironment(console=mock_console, system=mock_system)
        )
    )
    assert output == 42
    assert mock_console.effects == [
        console_effect.Input("How much wood would a woodchuck chuck?", "bad"),
        console_effect.Input("How much wood would a woodchuck chuck?", "input"),
        console_effect.Input("How much wood would a woodchuck chuck?", "")
    ]
    assert mock_console.user_input == []


def test_get_input_from_console_default_2() -> None:
    program = console.get_input_from_console(
        prompt="How much wood would a woodchuck chuck?",
        parse_value=ZIO.from_callable(str).map(int).catch(ValueError).either().to_callable(),
        default_value=None
    )

    mock_console = MockConsole(["bad", "input", "", "42"])
    mock_system = MockSystem()
    output = unsafe_run(
        program.provide(
            ConsoleSystemEnvironment(console=mock_console, system=mock_system)
        )
    )
    assert output == 42
    assert mock_console.effects == [
        console_effect.Input("How much wood would a woodchuck chuck?", "bad"),
        console_effect.Input("How much wood would a woodchuck chuck?", "input"),
        console_effect.Input("How much wood would a woodchuck chuck?", ""),
        console_effect.Input("How much wood would a woodchuck chuck?", "42")
    ]
    assert mock_console.user_input == []


def test_get_input_from_console_eof_error() -> None:
    program = console.get_input_from_console(
        prompt="How much wood would a woodchuck chuck?",
        parse_value=ZIO.from_callable(str).map(int).catch(ValueError).either().to_callable(),
        default_value=None
    )

    exception = EOFError()

    mock_console = MockConsole(["bad", "input", exception])
    mock_system = MockSystem()
    with pytest.raises(SystemExit):
        unsafe_run(
            program.provide(
                ConsoleSystemEnvironment(console=mock_console, system=mock_system)
            )
        )

    assert mock_console.effects == [
        console_effect.Input("How much wood would a woodchuck chuck?", "bad"),
        console_effect.Input("How much wood would a woodchuck chuck?", "input"),
        console_effect.Input("How much wood would a woodchuck chuck?", exception),
        console_effect.Print("")
    ]
    assert mock_console.user_input == []

    assert mock_system.effects == [
        system_effect.Exit(None)
    ]


@pytest.mark.parametrize(
    "user_input,default_value,expected_output",
    (
        ([''], 'y', True),
        ([''], 'n', False),
        (['y'], 'y', True),
        (['n'], 'n', False),
        (['y'], 'n', True),
        (['n'], 'y', False),

        (['Y'], 'y', True),
        (['N'], 'n', False),
        (['Y'], 'n', True),
        (['N'], 'y', False),

        (['asdf', 'Y'], 'y', True),
        (['asdf', 'N'], 'n', False),
        (['asdf', 'Y'], 'n', True),
        (['asdf', 'N'], 'y', False),
    )
)
def test_ask(
    user_input: List[Union[EOFError, KeyboardInterrupt, str]],
    default_value: Literal['y', 'n'],
    expected_output: bool
) -> None:
    program = console.ask(prompt="Are you having fun yet?", default=default_value)

    mock_console = MockConsole(user_input)
    mock_system = MockSystem()

    output = unsafe_run(
        program.provide(
            ConsoleSystemEnvironment(console=mock_console, system=mock_system)
        )
    )
    assert output == expected_output
    assert mock_console.user_input == []
    assert mock_system.effects == []
