from abc import ABCMeta, abstractmethod
from typing import NoReturn, TypeVar

from zio_py.zio import ZIO, ZIOStatic

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


def print_line(line: str) -> ZIO[Console, NoReturn, None]:
    return ZIOStatic.access_m(lambda env: env.print(line))


def read_line(prompt: str) -> ZIO[Console, Exception, str]:
    return ZIOStatic.access_m(lambda env: env.input(prompt))
