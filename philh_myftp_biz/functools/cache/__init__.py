from functools import cached_property as _cached_property
from _frozen_importlib import _module_locks
from os.path import dirname, join
from os import makedirs, getcwd
from diskcache import Cache
from sys import modules
from typing import Any

from .transitory import TransitoryCache # pyright: ignore[reportUnusedImport]

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

def clear_cache(instance: Any) -> None:

    for name, value in vars(instance).items():

        if isinstance(value, _cached_property):

            delattr(instance, name)

# ======================================
# cache_dir

_module = modules.get('__main__')

if _module is None:
    __fullname: str = next(iter(_module_locks), '')
    __name: str = __fullname.split('.')[0]
    _module = modules.get(__name)

if hasattr(_module, '__file__'):
    cache_dir = dirname(_module.__file__)
else:
    cache_dir = getcwd()

cache_dir = join(cache_dir, '/__pycache__/')
makedirs(cache_dir, exist_ok=True)

# ======================================

diskcache = Cache(cache_dir).memoize

