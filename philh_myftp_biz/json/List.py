from typing import Callable, Any, Self, Iterable, overload, cast
from .Collection import Collection

class List[V](Collection[V, list[V]]):

    _default: list[Any] = []

    @overload
    def __getitem__(self, key: int) -> V: ...

    @overload
    def __getitem__(self, key: slice) -> list[V]: ...

    def __getitem__(self, key: int | slice) -> V | list[V]:
        return self.read()[key]

    def extend(self, items: Iterable[V]) -> None:
        with self.handle() as data:
            data.extend(items)

    def pop(self, i: int = -1, n: int = 1) -> tuple[V, ...]:
        with self.handle() as data:
            n = min(n, len(data))
            return tuple(data.pop(i) for _ in range(n))

    def __iadd__(self, value: V) -> Self:
        with self.handle() as data:
            data.append(value)
        return self
    
    def __isub__(self, value: V) -> Self:
        with self.handle() as data:
            data.remove(value)
        return self
        
    #=======================================

    def sorted(self, func: Callable[[V], Any] = lambda x: x) -> 'List[V]':
        sdata = sorted(self.read(), key=func)
        return List(sdata)
    
    def sort(self, func: Callable[[V], Any] = lambda x: x) -> None:
        self.save(self.sorted(func))

    #=======================================

    def max(self, func: Callable[[V], Any] = lambda x: x) -> None | V:
        if len(self.read()) > 0:
            return max(self.read(), key=func)
        return None
    
    #=======================================

    def filtered(self, func: Callable[[V], Any] = lambda x: x) -> 'List[V]':
        return List(filter(func, self.read()))
    
    def filter(self, func: Callable[[V], Any] = lambda x: x) -> None:
        self.save(self.filtered(func))

    #=======================================

    def reversed(self) -> 'List[V]':
        cp = cast(List[V], self.copy())
        cp.reverse()
        return cp
    
    def reverse(self) -> None:
        with self.handle() as data:
            data.reverse()

    #=======================================

    def random(self) -> None | V:
        from random import choice
        data = self.read()
        if len(data) > 0:
            return choice(data)
        return None

    #=======================================

    def shuffled(self) -> 'List[V]':
        cp = cast(List[V], self.copy())
        cp.shuffle()
        return cp
    
    def shuffle(self) -> None:
        from random import shuffle
        with self.handle() as data:
            shuffle(data)

    #=======================================

    def uniquified(self, func: Callable[[V], Any] = lambda x: x) -> 'List[V]':
        data: dict[Any, V] = {}
        for item in self.read():
            data[func(item)] = item
        return List(data.values())
    
    def uniquify(self, func: Callable[[V], Any] = lambda x: x) -> None:
        self.save(self.uniquified(func))

    #=======================================

    def flattened(self) -> 'List[Any]':
        from itertools import chain
        return List(chain.from_iterable(self.read()))
    
    def flatten(self) -> None:
        self.save(cast(list[V], self.flattened().read()))

    #=======================================
