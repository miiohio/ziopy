from zio_py.services.console import MockConsole
from zio_py.services.system import MockSystem
from zio_py.environments import HasConsole, HasSystem, HasConsoleSystem


def test_has_console() -> None:
    con = MockConsole()
    env = HasConsole(console=con)
    assert env == {'console': con}


def test_has_system() -> None:
    sys = MockSystem()
    env = HasSystem(system=sys)
    assert env == {'system': sys}


def test_has_console_system() -> None:
    con = MockConsole()
    sys = MockSystem()
    env = HasConsoleSystem(console=con, system=sys)
    assert env == {'console': con, 'system': sys}
