from typing import Any, Generator, Callable, Type
from functools import cached_property as _cached_property

from .TransitoryCache import TransitoryCache # pyright: ignore[reportUnusedImport]
from .Absorber import Absorber, NullSafe # pyright: ignore[reportUnusedImport]
from .SharedBuffer import SharedBuffer # pyright: ignore[reportUnusedImport]
from .attr import attr, dunders, LinkedProperty # pyright: ignore[reportUnusedImport]
from .Partial import Partial # pyright: ignore[reportUnusedImport]
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

def copy_attrs(
    src: Any, 
    dst: Any, 
    force: bool = False
) -> None:
    for name, value in vars(src).items():
        if force or not hasattr(dst, name):
            setattr(dst, name, value)

class cached_property(_cached_property):

    def __new__(cls, *_, **__) -> _cached_property:
        return super().__new__(cls)

    def __set__(self, inst, value) -> None:
        inst.__dict__[self.attrname] = value

    def __delete__(self, inst) -> None:
        inst.__dict__.pop(self.attrname, None)

def attrs(obj:Any) -> Generator[attr, Any, None]:
    """Get all attributes of an instance or object"""

    for name in dir(obj):

        yield attr(obj, name)

def cpath(obj) -> str:
    """
    Class Path

    Ex: `cpath(print) -> '__builtins__.print'`
    """
    from types import FunctionType

    if not isinstance(obj, (type, FunctionType)):
        obj = obj.__class__

    return obj.__module__ + '.' + obj.__qualname__

def spath(x:int) -> str:
    """
    Stack Path

    Ex: `spath(0) -> 'test.py:14'`
    """
    from traceback import extract_stack

    stack = filter(
        lambda x: "<frozen " not in x.filename, 
        extract_stack()
    )

    frame = list(stack)[x]

    return f'{frame.filename.split('\\')[-1]}:{frame.lineno}'

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

        if isinstance(value, _cached_property):

            delattr(instance, name)

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

