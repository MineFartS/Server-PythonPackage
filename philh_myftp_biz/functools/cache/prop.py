from functools import cached_property as _cached_property

class cached_property[T](_cached_property[T]):

    def __init__(self, func):

        if not callable(func):
            func = lambda s: func

        super().__init__(func)

    def __new__(cls, *_, **__) -> _cached_property:
        return super().__new__(cls)

    def __set__(self, inst, value) -> None:
        inst.__dict__[self.attrname] = value

    def __delete__(self, inst) -> None:
        inst.__dict__.pop(self.attrname, None)
    
    def setter(self, fset):
        return type(self)(self.func, fset=fset)

