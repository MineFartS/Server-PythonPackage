from dataclasses import dataclass
from typing import Any

@dataclass
class Absorber[T]:
    """Returns all getattribute requests with a blank function that absorbs all params"""

    returns: T = lambda *args, **kwargs: None

    def __call__(self, *args, **kwargs) -> T:
        return self.returns

    __getattr__ = __call__

    __getitem__ = __call__

    __setitem__ = __call__

    __setitem__ = __call__

# @dataclass raises TypeError
class NullSafe:
    
    def __init__(self, 
        item: Any, 
        attr: str = None
    ) -> None:
        self.__parent = item
        self.__attr = attr

    @property
    def __item(self):
        if self.__attr:
            return getattr(self.__parent, self.__attr, None)
        else:
            return self.__parent

    def __getattr__(self, name:str):

        item = self.__item

        if item is None:
            return NullSafe(None)
        else:
            return getattr(item, name, None)
        
    def __call__(self, *args, **kwargs):
        
        item = self.__item

        if callable(item):
            item(*args, **kwargs)
        else:
            return NullSafe(None)

