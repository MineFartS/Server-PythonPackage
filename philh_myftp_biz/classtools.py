from typing import Any, Generator, Callable, Type
from functools import cached_property
from dataclasses import dataclass
import builtins

#========================================================

@dataclass
class attr:
    """Attribute of Instance/Object"""

    parent: Any
    name: str

    @cached_property
    def private(self) -> bool:

        if self.name.startswith('__'):
            return True

        elif hasattr(self.parent, '__name__') and (self.name.startswith(f'_{self.parent.__name__}__')):
            return True

        elif (self.name.startswith(f'_{self.parent.__class__.__name__}__')):
            return True

        else:
            
            for base in self.parent.__class__.__bases__:

                if self.name.startswith(f'_{base.__name__}__'):
                
                    return True
                
        return False

    @cached_property
    def value(self):
        
        if not self.private:

            try:
                return getattr(self.parent, self.name)
            except:
                pass

    @cached_property
    def callable(self):
        return callable(self.value)
    
    @cached_property
    def parameters(self) -> list[str]:
        from inspect import signature, ismethod

        try:

            keys = signature(self.value).parameters.keys()

            if ismethod(self.value):
                return list(keys)[1:]
            
            else:
                return list(keys)
        
        except ValueError, TypeError:

            return []

    @cached_property
    def null(self):
        return (self.value is None)

    def set(self, value:Any) -> None:

        if self.name in base_attrs:
    
            self.parent.__class__ = type(
                self.parent.__class__.__name__,
                (self.parent.__class__,),
                {self.name: value}
            )

        else:

            setattr(self, self.name, value)

    def __str__(self) -> str:
        """
        Get the value of the attribute as a string

        Formats with json.dumps
        """
        from .json import dumps

        try:
            return dumps(
                obj = self.value,
                indent = 2
            )
        except TypeError:
            return str(self.value)

#========================================================

base_attrs: list[str] = []

for obj in vars(builtins).values():
    base_attrs += dir(obj)

base_attrs = list(set(n for n in base_attrs if n.startswith('__')))

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

class SharedBuffer:

    stop_when: Callable[[], bool] = lambda: False
    """
    Is called before each iteration
    Will stop iteration if returns True 
    """

    def __init__(self) -> None:
        
        self.entries = []

        self.__iadd__ = self.entries.append

        self.add = self.entries.append

    def __iter__(self):
        return self

    def __next__(self):

        if self.stop_when():

            raise StopIteration()
        
        else:

            while len(self.entries) == 0:
                pass

            entry = self.entries[0]

            del self.entries[0]

            return entry

#========================================================

def clear_cache(instance: Any) -> None:

    for name, value in vars(instance).items():

        if isinstance(value, cached_property):

            delattr(instance, name)

#========================================================

def singleton[T](cls:Type[T]) -> T:
    return cls()

#========================================================

class Absorber:
    """Returns all getattribute requests with a blank function that absorbs all params"""

    def __getattr__(self, *_) -> Callable[..., None]:
        return lambda *args, **kwargs: None

#========================================================
