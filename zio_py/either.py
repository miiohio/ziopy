from abc import ABCMeta, abstractmethod
from typing import Callable, Generic, TypeVar

A = TypeVar('A', covariant=True)
B = TypeVar('B', covariant=True)
C = TypeVar('C', covariant=True)

class Either(Generic[A, B], metaclass=ABCMeta):
    def fold(self, left: Callable[[A], C], right: Callable[[B], C]) -> C:
        # TODO
        pass
