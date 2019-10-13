from abc import ABCMeta, abstractmethod
from typing import Generic, NoReturn, TypeVar

from zio_py.either import Either

E = TypeVar('E', covariant=True)


class Cause(Generic[E], metaclass=ABCMeta):
    @abstractmethod
    def failure_or_cause(self) -> Either[E, 'Cause[NoReturn]']:
        # TODO
        pass


class Die(Cause[NoReturn]):
    value: Exception
