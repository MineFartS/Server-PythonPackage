from typing import Callable, Any, Iterator, Self

#========================================================

class List[V]:
    """
    List/Tuple Wrapper

    Stores data to the local disk instead of memory
    """

    read: Callable[[], list[V]]
    """Read Data"""

    save: Callable[[list[V]], None]
    """Save Data"""

    def __init__(self,
        a: Iterator[V] | list[V] | tuple[V] = []
    ) -> None:
        from .file import PKL, temp

        if isinstance(a, List):
            self.var = a.var

        elif hasattr(a, 'read') and hasattr(a, 'save'):
            self.var = a

        else:
            self.var = PKL(
                path = temp('array', 'pkl'),
                default = list(a)
            )
        
        self.read = self.var.read
        self.save = self.var.save

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

    def sorted(self,
        func: Callable[[V], Any] = lambda x: x
    ) -> List[V]:
        
        data: list[V] = self.read()

        sdata = sorted(data, key=func)

        return List(sdata)

    def sort(self,
        func: Callable[[V], Any] = lambda x: x
    ) -> None:
        
        data: list[V] = self.sorted().read()

        self.save(data)

    def max(self,
        func: Callable[[V], Any] = lambda x: x
    ) -> None | V:
        
        if len(self) > 0:

            return max(
                self.read(),
                key = func
            )
    
    def filtered(self,
        func: Callable[[V], Any] = lambda x: x
    ) -> List[V]:

        filtered: filter[V] = filter(func, self.read())

        return List(filtered)
    
    def filter(self,
        func: Callable[[V], Any] = lambda x: x
    ) -> None:
        
        data: list[V] = self.filtered(func=func).read()

        self.save(data)

    def reversed(self) -> List[V]:

        data: list[V] = self.read()

        data.reverse()

        return List(data)
    
    def reverse(self):

        data: list[V] = self.reversed().read()

        self.save(data)

    def random(self) -> None | V:
        from random import choice

        data: list[V] = self.read()

        if len(data) > 0:
            return choice(data)

    def shuffled(self) -> List[V]:
        from random import shuffle

        data: list[V] = self.read()

        shuffle(data)

        return List(data)

    def shuffle(self) -> None:

        data: list[V] = self.shuffled().read()

        self.save(data)

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