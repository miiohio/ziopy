import sys
from abc import ABCMeta, abstractmethod
from typing import List, NoReturn, Optional
from typing_extensions import Protocol

import ziopy.services.mock_effects.system as system_effect
from ziopy.zio import ZIO, Environment


class System(metaclass=ABCMeta):
    @abstractmethod
    def exit(self, exit_code: Optional[int] = None) -> ZIO[object, NoReturn, NoReturn]:
        pass  # pragma: nocover


class LiveSystem(System):
    def exit(self, exit_code: Optional[int] = None) -> ZIO[object, NoReturn, NoReturn]:
        return ZIO.effect_total(lambda: sys.exit(exit_code))  # type: ignore


class MockSystem(System):
    def __init__(self) -> None:
        self._effects: List[system_effect.Exit] = []

    def exit(self, exit_code: Optional[int] = None) -> ZIO[object, NoReturn, NoReturn]:
        self._effects.append(system_effect.Exit(exit_code))
        return ZIO.fail(SystemExit(exit_code)).or_die()

    @property
    def effects(self) -> List[system_effect.Exit]:
        return self._effects


class HasSystem(Protocol):
    @property
    def system(self) -> System:
        pass  # pragma: nocover


def exit(exit_code: Optional[int] = None) -> ZIO[HasSystem, NoReturn, NoReturn]:
    return Environment[HasSystem]().flat_map(lambda env: env.system.exit(exit_code))
