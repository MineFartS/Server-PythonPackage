from .functools.supports import SupportsJSON # pyright: ignore[reportUnusedImport]
from json import load, loads, dump, dumps # pyright: ignore[reportUnusedImport]
from typing import Callable, Any, Iterator, Self, ItemsView, Callable
from functools import partialmethod

#========================================================

def is_json(value:str) -> bool:
    """Check if a string contains valid json data"""
    from json.decoder import JSONDecodeError

    try:
        loads(value)
        return True
    except JSONDecodeError:
        return False

#========================================================

class Collection[T, STRUCT]:

    _default: T

    def __init__(self,
        t: STRUCT = None
    ) -> None:
        from .file import PKL, temp

        if isinstance(t, Collection):
            self.var = t.var

        elif hasattr(t, 'read') and hasattr(t, 'save'):
            self.var = t

        else:

            if isinstance(t, (tuple, filter)):
                t = list(t)

            self.var = PKL(
                path = temp('Collection', 'pkl')
            )
            self.var.save(t)

        self.var.default = self._default

        self.read: Callable[[], STRUCT] = self.var.read
        
        self.save: Callable[[STRUCT], None] = self.var.save
    
    def __len__(self) -> int:
        return len(self.read())
        
    def __setitem__(self, key, value:T) -> None:

        # Get the raw dictionary
        data: STRUCT = self.read()

        # Update the key with the value
        data[key] = value

        # Save the raw dictionary
        self.save(data)

    def __delitem__(self, key) -> None:
        
        # Get the raw dictionary
        data: STRUCT = self.read()
        
        # Remove the key
        del data[key]
        
        # Save the dictionary
        self.save(data)

    def __contains__(self, key) -> bool:
        return (key in self.read())
    
    def __str__(self) -> str:
        return dumps(
            obj = self.read(),
            indent = 2
        )
    
    __repr__ = __str__

#========================================================

class Dict[T](Collection[T, dict[str, T]]):
    """dict Wrapper"""
    
    _default = {}

    def __getitem__(self, key) -> None | T:
        
        data = self.read()
        
        if key in data:
            return data[key]
        
    def __iter__(self):
        return iter(self.read().keys())

    def items(self) -> ItemsView[str, T]:
        return self.read().items()

#========================================================

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

        data: list[V] = self.read()[key]

        if isinstance(key, slice):
            return List(data)
        else:
            return data[key]

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

#========================================================
