from typing import Callable, Self, TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .file import JSON, PKL, TXT
    from .pc import _var

class InvalidArrayError(Exception):
    pass

class List[V]:
    """
    List/Tuple Wrapper

    Stores data to the local disk instead of memory
    """

    def __init__(self,
        array: 'list[V] | tuple[V] | Self[V] | filter[V] | JSON | _var | PKL | range' = []
    ):
        from .file import JSON, PKL, temp, TXT
        from builtins import filter
        from .classOBJ import path
        from .pc import _var

        if isinstance(array, (JSON, _var, PKL, TXT)):
            self.var = array

        elif isinstance(array, List):
            self.var = array.var

        elif isinstance(array, (list, tuple, filter, range)):
            self.var = PKL(
                temp('array', 'pkl')
            )
            self.var.save(list(array))

        else:

            raise InvalidArrayError(path(array))

    def save(self, data:list[V]) -> None:
        """Save Data"""
        self.var.save(data)

    def read(self) -> list[V]:
        """Read Data"""
        return self.var.read()
    
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

    remove = __delitem__

    def __iadd__(self, value:V):
        
        data = self.read()
        
        data.append(value)
        
        self.save(data)

        return self
    
    append = __iadd__

    def __isub__(self, value:V):

        if isinstance(value, (list, tuple)):
            for item in value:
                self.remove(item)
        else:
            self.remove(value)

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
            return self.sorted(func)[0]
    
    def filtered(self,
        func: Callable[[V], Any] = lambda x: x
    ) -> Self[V]:
        from builtins import filter

        return List(filter(
            function = func,
            iterable = self.read()
        ))
    
    def filter(self,
        func: Callable[[V], Any] = lambda x: x
    ) -> None:
        self.save(list(filter(
            function = func,
            iterable = self.read()
        )))

    def reversed(self):

        data = self.read()

        data.reverse()

        return List(data)
    
    def reverse(self):

        data = self.read()

        data.reverse()

        self.save(data)

    def random(self) -> None | V:
        from random import choice

        data = self.read()

        if len(data) > 0:
            return choice(data)

    def shuffle(self) -> None:
        from random import shuffle

        data = self.read()

        shuffle(data)
        
        self.save(data)
    
    def shuffled(self) -> Self[V]:
        from random import shuffle

        data = self.read()

        shuffle(data)

        return List(data)

    def __str__(self) -> str:
        from .json import dumps

        return dumps(self.read(), indent=2)
    
    def value_in_common(self,
        array: list | List
    ) -> bool:
        
        for v in self.read():
            if v in array:
                return True
        
        return False

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
