from typing import Any, Callable, Type

from .TransitoryCache import TransitoryCache # pyright: ignore[reportUnusedImport]
from .Absorber import Absorber, NullSafe # pyright: ignore[reportUnusedImport]
from .SharedBuffer import SharedBuffer # pyright: ignore[reportUnusedImport]
from .attr import attr, dunders, LinkedProperty, attrs # pyright: ignore[reportUnusedImport]
from .Partial import Partial # pyright: ignore[reportUnusedImport]
from .paths import cpath, spath # pyright: ignore[reportUnusedImport]
from .cache import cached_property, clear_cache # pyright: ignore[reportUnusedImport]
from .supports import *

def is_iterable(obj) -> bool:
    """*Ignores strings"""
    
    if isinstance(obj, (str, bytes, bytearray)):
        return False
    
    try:
        iter(obj)
        return True
    except TypeError:
        return False

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

def force_types(func):
    """
    Forces parameter types
    
    EXAMPLE:
    ```
    @force_types
    def myfunc(x: int, y: float):
        ...
    
    myfunc('1', '2') -> myfunc(int('1'), float('2'))
    myfunc(3, '4') -> myfunc(3, float('4'))
    """
    from inspect import signature
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):

        bargs = signature(func).bind(*args, **kwargs)
        bargs.apply_defaults()

        for name, value in bargs.arguments.items():

            etype = func.__annotations__.get(name)

            if etype and not isinstance(value, etype):
                bargs.arguments[name] = etype(value)

        return func(*bargs.args, **bargs.kwargs)
    
    return wrapper

def waitfor(
    func: Callable[..., bool]
) -> None:

    while not func():
        pass

def copy_attrs(
    src: Any, 
    dst: Any, 
    force: bool = False
) -> None:
    for name, value in vars(src).items():
        if force or not hasattr(dst, name):
            setattr(dst, name, value)

def loc(obj:Any) -> str:
    """Get the hexadecimal location of an instance in memory"""
    return hex(id(obj))

class LockingClass:

    _locked = False

    def lock(self):
        self.__dict__['_locked'] = True

    def unlock(self):
        self.__dict__['_locked'] = False

    def __setattr__(self, key, value):
        if self._locked:
            raise AttributeError("This object is read-only")
        else:
            super().__setattr__(key, value)

#========================================================

def stringify(obj:Any) -> str:
    """Creates a string table of all attributes of an instance"""

    string = f'--- {cpath(obj)} @{loc(obj)} ---\n'

    for c in attrs(obj):

        if not (c.private or c.callable or c.null):

            string += f'{c.name} = {c}\n'

    return string

#========================================================

def singleton[T](
    cls: Type[T] | Callable[..., T]
) -> T:
    return cls()

#========================================================

def return_type[T](func: Callable[..., T]) -> None | Type[T]:
    from inspect import getsource
    import ast

    source = getsource(func)
    tree = ast.parse(source)

    # Find the return node and guess its type
    for node in ast.walk(tree):
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Constant):
            return type(node.value.value) # pyright: ignore[reportReturnType]

