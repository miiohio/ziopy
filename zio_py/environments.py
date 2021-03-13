from typing_extensions import TypedDict

import zio_py.services.console as console
import zio_py.services.system as system


class HasConsole(TypedDict):
    console: console.Console


class HasSystem(TypedDict):
    system: system.System


class HasConsoleSystem(HasConsole, HasSystem):
    pass
