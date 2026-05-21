from typing import Any, Generator, Callable, Type
from functools import cached_property

from .TransitoryCache import TransitoryCache # pyright: ignore[reportUnusedImport]
from .Absorber import Absorber # pyright: ignore[reportUnusedImport]
from .SharedBuffer import SharedBuffer # pyright: ignore[reportUnusedImport]
from .attr import attr, base_attrs # pyright: ignore[reportUnusedImport]
from .supports import *

#========================================================

def single_use(f): # pyright: ignore[reportMissingParameterType]
    """Ignore all but first executions"""
    from functools import wraps

    @wraps(f)
    def wrapper(*args, **kwargs): # pyright: ignore[reportMissingParameterType]
        
        if not wrapper.has_run:
            
            wrapper.has_run = True
            
            return f(*args, **kwargs)
    
    wrapper.has_run = False

    return wrapper

def waitfor(
    func: Callable[..., bool]
) -> None:

    while not func():
        pass

#========================================================

def attrs(obj:Any) -> Generator[attr, Any, None]:
    """Get all attributes of an instance or object"""

    for name in dir(obj):

        yield attr(obj, name)

def cpath(obj:Any) -> str:
    """
    Get Full path of instance

    Ex: path(print) -> '__builtins__.print'
    """

    return obj.__class__.__module__ + '.' + obj.__class__.__qualname__

def loc(obj:Any) -> str:
    """Get the hexadecimal location of an instance in memory"""
    return hex(id(obj))

#========================================================

def stringify(obj:Any) -> str:
    """Creates a string table of all attributes of an instance"""

    string = f'--- {cpath(obj)} @{loc(obj)} ---\n'

    for c in attrs(obj):

        if not (c.private or c.callable or c.null):

            string += f'{c.name} = {c}\n'

    return string

#========================================================

def clear_cache(instance: Any) -> None:

    for name, value in vars(instance).items():

        if isinstance(value, cached_property):

            delattr(instance, name)

#========================================================

def singleton[T](
    cls: Type[T] | Callable[..., T]
) -> T:
    return cls()

#========================================================

