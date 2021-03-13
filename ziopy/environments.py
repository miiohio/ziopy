from dataclasses import dataclass

import ziopy.services.console as console
import ziopy.services.system as system


@dataclass(frozen=True)
class ConsoleEnvironment:
    console: console.Console


@dataclass(frozen=True)
class SystemEnvironment:
    system: system.System


@dataclass(frozen=True)
class ConsoleSystemEnvironment(ConsoleEnvironment, SystemEnvironment):
    pass
