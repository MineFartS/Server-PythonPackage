from typing import Callable, Any, Iterator, Self, Union, TypeAlias, TypeVar
from functools import partialmethod

_T = TypeVar('_T')

SortFunc: TypeAlias = Callable[
    [_T],
    Union[
        int, 
        float, 
        list[int | float], 
        tuple[int | float]
    ]
]

FilterFunc: TypeAlias = Callable[[_T], bool]

#========================================================

class List[V]:
    """List/Tuple Wrapper"""

    read: Callable[[], list[V]]
    """Read Data"""

    save: Callable[[list[V]], None]
    """Save Data"""

    def __init__(self,
        a: Iterator[V] | list[V] | tuple[V] = []
    ) -> None:

        if hasattr(a, 'read') and hasattr(a, 'save'):
        
            if isinstance(a, List):
                a = a.var
                
            self.var = a

            if a.default is None:
                a.default = []

            self.read = self.var.read
            self.save = self.var.save

        else:
            
            self.read = lambda: self.var

            self.save = lambda x: setattr(self, 'var', list(x))

            self.save(a)

    def __iter__(self) -> Iterator[V]:
        return iter(self.read())

    def __len__(self) -> int:
        return len(self.read())
    
    def __getitem__(self,
        key: int|slice
    ) -> V | List[V]:

        data: list[V] = self.read()[key]

        if isinstance(key, slice):
            return List(data)
        else:
            return data[key]

    def __setitem__(self,
        key: int,
        value: V
    ) -> None:
        
        data: list[V] = self.read()

        data[key] = value
        
        self.save(data)

    def __delitem__(self, key:int) -> None:
        
        data: list[V] = self.read()

        del data[key]

        self.save(data)

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

    def __contains__(self, value:V) -> bool:
        return (value in self.read())
    
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

        data: list[V] = set(self.read())

        return List(data)

    uniquify = __updater(uniquified)

    #=======================================

    def flattened(self) -> List[V]:
        from itertools import chain

        data: chain[V] = chain.from_iterable(self.read())

        return List(data)

    flatten = __updater(flattened)

    #=======================================

    def __str__(self) -> str:
        from .json import dumps

        return dumps(
            obj = self.read(),
            indent = 2
        )
    
    __repr__ = __str__

#========================================================

def copy(
    array: list|tuple
) -> list:
    
    if isinstance(array, list):
        return array.copy()
    
    else:
        return list(array[:])

def stringify(array:list) -> list[str]:

    array = copy(array)

    for x, item in enumerate(array):
        array[x] = str(item)

    return array

def intify(array:list) -> list[int]:

    array = copy(array)

    for x, item in enumerate(array):
        array[x] = int(item)

    return array

#========================================================

def overlap(
    list1: list,
    list2: list
) -> bool:
    return not set(list1).isdisjoint(list2)

#========================================================
