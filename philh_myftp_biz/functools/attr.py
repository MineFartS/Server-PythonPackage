from functools import cached_property
from dataclasses import dataclass
from typing import Any, Generator
import builtins

#========================================================

dunders: list[str] = []

for obj in vars(builtins).values():
    dunders += dir(obj)

dunders = list(set(n for n in dunders if n.startswith('__')))

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
        
        except (ValueError, TypeError):

            return []

    @cached_property
    def null(self):
        return (self.value is None)

    def set(self, value:Any) -> None:

        if self.name in dunders:
    
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
        from ..json import dumps

        try:
            return dumps(
                obj = self.value,
                indent = 2
            )
        except TypeError:
            return str(self.value)

def attrs(obj:Any) -> Generator[attr, Any, None]:
    """Get all attributes of an instance or object"""

    for name in dir(obj):

        yield attr(obj, name)

#========================================================

class LinkedProperty(property):

    def __init__(self,
        obj: Any,
        name: str
    ) -> None:
        super().__init__()
        self.obj = obj
        self.name = name

    def fset(self, value):
        setattr(self.obj, self.name, value)

    def fget(self, default=None):
        return getattr(self.obj, self.name, default)


