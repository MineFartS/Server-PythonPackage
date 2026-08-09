from typing import Self, Any, cast, Generator, Iterator
from contextlib import contextmanager
from ..file import _Template as File
from json import dumps

class Collection[T, STRUCT]:

    _default: STRUCT

    _cache: STRUCT

    var: File

    def __init__(self,
        t: STRUCT | File | 'Collection[T, STRUCT]' | Any = None
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
            self._cache = cast(STRUCT, list(t))
        
        elif t is None:
            self._cache = self._default
        
        else:
            self._cache = cast(STRUCT, t)
        
        self.__backup = self.read()

    def read(self) -> STRUCT:
        from copy import deepcopy
        return deepcopy(self._cache)
    
    @contextmanager
    def handle(self) -> Generator[STRUCT, None, None]:
        data = self.read()
        try:
            yield data
        finally:
            self.save(data)
    
    def save(self, data: STRUCT | 'Collection[T, STRUCT]') -> None:

        if isinstance(data, Collection):
            data = data.read()

        self._cache = data

        if hasattr(self, 'var'):
            self.var.save(data)
    
    def copy(self) -> Self:
        return self.__class__(self.read())

    def __len__(self) -> int:
        return len(self.read())  # type: ignore
        
    def __setitem__(self, key: Any, value: T) -> None:
        with self.handle() as data:
            data[key] = value  # type: ignore

    def __delitem__(self, key: Any) -> None:
        with self.handle() as data:
            del data[key]  # type: ignore

    def __contains__(self, key: Any) -> bool:
        return (key in self.read())  # type: ignore
    
    def __str__(self) -> str:
        return dumps(
            obj = self.read(),
            indent = 2
        )
    
    __repr__ = __str__

    def __iter__(self) -> Iterator[T]:
        return iter(self.read())

    def reset(self) -> None:
        self.save(self.__backup)
