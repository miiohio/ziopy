import pytest
from unittest.mock import patch

import zio_py.services.system as system
import zio_py.services.mock_effects.system as system_effect
from zio_py.environments import SystemEnvironment
from zio_py.zio import unsafe_run
from zio_py.services.system import LiveSystem, MockSystem


def test_live_system_exit_without_running() -> None:
    with patch('sys.exit') as mock_exit:
        system.exit(0).provide(SystemEnvironment(LiveSystem()))
    mock_exit.assert_not_called()


def test_live_system_exit_with_running() -> None:
    with patch('sys.exit') as mock_exit:
        program = system.exit(1).provide(SystemEnvironment(LiveSystem()))
        unsafe_run(program)
    mock_exit.assert_called_with(1)


def test_mock_system_exit() -> None:
    mock_system = MockSystem()
    program = system.exit(1).provide(SystemEnvironment(mock_system))
    with pytest.raises(SystemExit):
        unsafe_run(program)

    assert mock_system.effects == [
        system_effect.Exit(1)
    ]
