from abc import ABCMeta, abstractmethod
from typing import NoReturn, TypeVar

from zio.zio import ZIO, ZIOStatic

R = TypeVar('R')

class Console(metaclass=ABCMeta):
    @abstractmethod
    def print(self, line: str) -> ZIO[R, NoReturn, None]:
        pass

    @abstractmethod
    def input(self, prompt: str) -> ZIO[R, Exception, str]:
        pass

class LiveConsole(Console):
    def print(self, line: str) -> ZIO[R, NoReturn, None]:
        return ZIOStatic.effect_total(lambda: print(line))

    def input(self, prompt: str) -> ZIO[R, Exception, str]:
        return ZIOStatic.effect(lambda: input(prompt))
