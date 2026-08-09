from functools import cached_property as _cached_property
from typing import Any, Callable, overload

class cached_property[T](_cached_property[T]):

    @overload
    def __init__(self, func: Callable[[Any], T], /) -> None: ...

    @overload
    def __init__(self, func: T, /) -> None: ...

    def __init__(self, func):
        from weakreflist import WeakList

        if not callable(func):
            func = lambda s: func

        super().__init__(func)

        self._do_skip = WeakList()

    def __get__(self, inst, cls=None):

        if inst is None:
            return self
        
        elif inst in self._do_skip:
            self._do_skip.remove(inst)
            return self.func(inst)

        else:
            return super().__get__(inst, cls)

    def __set__(self, inst, value) -> None:
        inst.__dict__[self.attrname] = value

    def __delete__(self, inst) -> None:
        inst.__dict__.pop(self.attrname, None)
    
    def setter(self, fset):
        return type(self)(self.func, fset=fset)

    def skip_cache(self, inst):
        self.__delete__(inst)
        self._do_skip += [inst]

