from typing import Callable, Any, Iterator, Self, Callable
from functools import partialmethod
from .Collection import Collection

class List[V](Collection[V, list[V]]):
    """list Wrapper"""

    _default = []

    def read(self) -> list[V]:
        
        data = super().read()
        
        if data:
            return data
        else:
            return []

    def __iter__(self) -> Iterator[V]:
        return iter(self.read())
    
    def __getitem__(self,
        key: int|slice
    ) -> V | List[V]:

        data: V = self.read()[key]

        if isinstance(key, slice):
            return List(data)
        else:
            return data

    def __iadd__(self, value:V) -> Self:
        
        data: list[V] = self.read()
        
        data.append(value)
        
        self.save(data)

        return self
    
    def __isub__(self, value:V) -> Self:

        data: list[V] = self.read()
        
        data.remove(value)
        
        self.save(data)

        return self
    
    def __list__(self):
        return self.read()

    def __updater[T](
        _func: Callable[..., List[T]]
    ):

        def method(self:List[T], *args, **kwargs): # pyright: ignore[reportMissingParameterType]

            self.save(_func(self, *args, **kwargs).read())

            return self

        return partialmethod(method)
    
    #=======================================

    def sorted(self,
        func: Callable[[V], Any] = lambda x: x
    ) -> List[V]:
        
        data: list[V] = self.read()

        sdata = sorted(data, key=func)

        return List(sdata)

    sort = __updater(sorted)

    #=======================================

    def max(self,
        func: Callable[[V], Any] = lambda x: x
    ) -> None | V:
        
        if len(self) > 0:

            return max(
                self.read(),
                key = func
            )
    
    #=======================================

    def filtered(self,
        func: Callable[[V], Any] = lambda x: x
    ) -> List[V]:

        filtered: filter[V] = filter(func, self.read())

        return List(filtered)
    
    filter = __updater(filtered)

    #=======================================

    def reversed(self) -> List[V]:

        data: list[V] = self.read()

        data.reverse()

        return List(data)
    
    reverse = __updater(reversed)

    #=======================================

    def random(self) -> None | V:
        from random import choice

        data: list[V] = self.read()

        if len(data) > 0:
            return choice(data)

    #=======================================

    def shuffled(self) -> List[V]:
        from random import shuffle

        data: list[V] = self.read()

        shuffle(data)

        return List(data)

    shuffle = __updater(shuffled)

    #=======================================

    def uniquified(self) -> List[V]:

        data = List()

        for item in self.read():

            if item not in data:

                data += item

        return data

    uniquify = __updater(uniquified)

    #=======================================

    def flattened(self) -> List[V]:
        from itertools import chain

        data: chain[V] = chain.from_iterable(self.read())

        return List(data)

    flatten = __updater(flattened)

    #=======================================
