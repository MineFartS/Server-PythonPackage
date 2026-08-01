from ..file import _Template as File
from typing import Self
from json import dumps

class Collection[T, STRUCT]:

    _default: T

    _cache: None|STRUCT

    var: File

    def __init__(self,
        t: STRUCT | File = None
    ) -> None:
        from types import GeneratorType

        if isinstance(t, Collection):
            self.var = t.var
            self._cache = t.var.read()

        elif isinstance(t, File):
            t.default = self._default
            self.var = t
            self._cache = t.read()

        elif isinstance(t, (tuple, filter, GeneratorType)):
            self._cache = list(t)
        
        elif t is None:
            self._cache = self._default
        
        else:
            self._cache = t
        
        self.__backup = self._cache.copy()

    def read(self) -> STRUCT:
        return self._cache # pyright: ignore[reportReturnType]
    
    def save(self, data:'STRUCT|Collection') -> None:

        if isinstance(data, Collection):
            data = data.read()

        self._cache = data

        if hasattr(self, 'var'):
            self.var.save(data)
    
    def copy(self) -> Self:
        from copy import deepcopy
        data = deepcopy(self.read())
        return self.__class__(data)

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

    def reset(self):
        """
        Reset data to original input
        
        EXAMPLE: 
        ```
        l = List([1, 2, 3])
        l += 4
        l.read() -> [1, 2, 3, 4]
        l.reset()
        l.read() -> [1, 2, 3]
        ```
        """
        self.save(self.__backup)

