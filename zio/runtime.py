from typing import Any, Deque, List, TypeVar, Generic

from zio.zio import ZIO, FlatMap, EffectPartial, EffectTotal, Fail, MapFn, Fold, FoldCauseMFailureFn, Provide, Read, Succeed
from zio.either import Either
from zio.cause import Cause


A = TypeVar('A')
E = TypeVar('E')
R = TypeVar('R', covariant=True)

class Runtime(Generic[R]):
    def __init__(self) -> None:
        self.environments: List[Any] = []

    def unsafe_run_sync(self: 'Runtime[R]', zio: ZIO[Any, E, A]) -> A:
        if isinstance(zio, FlatMap):
            the_zio = zio.zio
            k = zio.k
            a = self.unsafe_run_sync(the_zio)
            return self.unsafe_run_sync(k(a)) # type: ignore
        elif isinstance(zio, EffectTotal):
            return zio.effect()
        elif isinstance(zio, EffectPartial):
            return zio.effect() # type: ignore
        elif isinstance(zio, Fail):
            raise zio.cause.value # type: ignore
        elif isinstance(zio, MapFn):
            return zio(a) # type: ignore
        elif isinstance(zio, Fold):
            value = self.unsafe_run_sync(zio.value)
            if isinstance(value, Cause):
                return self.unsafe_run_sync(zio.failure(value))
            else:
                return self.unsafe_run_sync(zio.success(value))
        elif isinstance(zio, Provide):
            self.environments.append(zio.r)
            # TODO: Bracket the environment
            return self.unsafe_run_sync(zio.next) # type: ignore
        elif isinstance(zio, Read):
            r = self.environments[-1]
            return self.unsafe_run_sync(zio.k(r)) # type: ignore
        elif isinstance(zio, Succeed):
            return zio.value
        else:
            raise ValueError(f"Unexpected instruction: {zio}")
