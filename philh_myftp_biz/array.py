from typing import Callable, Self, Any, Iterator

#========================================================

class List[V]:
    """
    List/Tuple Wrapper

    Stores data to the local disk instead of memory
    """

    def __init__(self,
        a: Iterator[V] | list[V] | tuple[V] = []
    ):
        from .file import PKL, temp
        from .classOBJ import path

        if isinstance(a, List):
            self.var = a.var

        elif hasattr(a, 'read') and hasattr(a, 'save'):
            self.var = a

        elif isinstance(a, (Iterator, list, tuple)):
            self.var = PKL(
                temp('array', 'pkl'),
                default = list(a)
            )

        else:
            raise TypeError(path(a))
        
        self.read: Callable[[], list[V]] = self.var.read
        """Read Data"""

        self.save: Callable[[list[V]], None] = self.var.save
        """Save Data"""
    
    def rm_duplicates(self):
        data = self.read()
        data_ = []
        for item in data:
            if item not in data_:
                data_.append(item)
        self.save(data_)

    def __iter__(self):
        return iter(self.read())

    def __len__(self) -> int:
        return len(self.read())
    
    def __getitem__(self, key:int) -> V:
        return self.read()[key]

    def __setitem__(self,
        key: int,
        value: V
    ):
        data = self.read()

        data[key] = value
        
        self.save(data)

    def __delitem__(self, key:int) -> None:
        
        data = self.read()

        del data[key]

        self.save(data)

    def __iadd__(self, value:V):
        
        data = self.read()
        
        data.append(value)
        
        self.save(data)

        return self
    
    def __isub__(self, value:V):

        data = self.read()
        
        data.remove(value)
        
        self.save(data)

        return self

    def __contains__(self, value:V):
        return (value in self.read())

    def sorted(self,
        func: Callable[[V], Any] = lambda x: x
    ) -> Self[V]:
        
        data = self.read()

        data = sorted(data, key=func)

        return List(data)

    def sort(self,
        func: Callable[[V], Any] = lambda x: x
    ) -> None:
        
        data = self.read()

        data = sorted(data, key=func)

        self.save(data)

    def max(self,
        func: Callable[[V], Any] = lambda x: x
    ) -> None | V:
        if len(self) > 0:
            return self.sorted(func)[-1]
    
    def filtered(self,
        func: Callable[[V], Any] = lambda x: x
    ) -> Self[V]:
        from builtins import filter

        return List(filter(func, self.read()))
    
    def filter(self,
        func: Callable[[V], Any] = lambda x: x
    ) -> None:
        
        l = self.filtered(func)

        self.save(l.read())

    def reversed(self):

        data = self.read()

        data.reverse()

        return List(data)
    
    def reverse(self):

        l = self.reversed()

        self.save(l)

    def random(self) -> None | V:
        from random import choice

        data = self.read()

        if len(data) > 0:
            return choice(data)

    def shuffled(self) -> Self[V]:
        from random import shuffle

        data = self.read()

        shuffle(data)

        return List(data)

    def shuffle(self) -> None:

        l = self.shuffled()

        self.save(l)

    def __str__(self) -> str:
        from .json import dumps

        return dumps(
            obj = self.read(),
            indent = 2
        )

#========================================================

def stringify(array:list) -> list[str]:

    array = array.copy()

    for x, item in enumerate(array):
        array[x] = str(item)

    return array

def intify(array:list) -> list[int]:

    array = array.copy()

    for x, item in enumerate(array):
        array[x] = int(item)

    return array

def auto_convert(array:list):
    from .text import auto_convert

    array = array.copy()

    for x, a in enumerate(array):
        array[x] = auto_convert(a)

    return array

def priority(
    _1: int,
    _2: int,
    reverse: bool = False
):  
    
    if _1 is None:
        _1 = 0

    if _2 is None:
        _2 = 0

    p = _1 + (_2 / (1000**1000))
    
    if reverse:
        p *= -1

    return p

#========================================================