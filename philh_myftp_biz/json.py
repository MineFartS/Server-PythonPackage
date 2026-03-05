from json import load, loads, dump, dumps # pyright: ignore[reportUnusedImport]
from typing import Any, ItemsView, Callable

#========================================================

def valid(value:str) -> bool:
    """
    Check if a string contains valid json data
    """
    from json import decoder

    try:
        loads(value)
        return True
    except decoder.JSONDecodeError:
        return False

#========================================================

class Dict[V]:
    """
    Dict Wrapper

    Stores data to the local disk instead of memory
    """

    read: Callable[[], dict[str, V]]
    """Read Data"""

    save: Callable[[dict[str, V]], None]
    """Save Data"""

    def __init__(self,
        t: Dict | dict[str,V] | Any = {}
    ) -> None:
        from .file import PKL, temp

        if isinstance(t, Dict):
            self.var = t.var

        elif hasattr(t, 'read') and hasattr(t, 'save'):
            self.var = t

        else:
            self.var = PKL(
                path = temp('table', 'json')
            )
            self.var.save(t)

        if self.var.default is None:
            self.var.default = {}

        self.read = self.var.read
        self.save = self.var.save

    def items(self) -> ItemsView[str, V]:
        return self.read().items()
    
    def __iter__(self):
        return iter(self.read())

    def __len__(self) -> int:
        return len(self.read().keys())
    
    def __getitem__(self, key:str) -> None | V:
        try:
            return self.read()[key]
        except KeyError:
            return None

    def __setitem__(self,
        key: str,
        value: V
    ) -> None:

        # Get the raw dictionary
        data: dict[str, V] = self.read()

        # Update the key with the value
        data[key] = value

        # Save the raw dictionary
        self.save(data)

    def __delitem__(self, key:str) -> None:
        
        # Get the raw dictionary
        arr: dict[str, V] = self.read()
        
        # Remove the key
        del arr[key]
        
        # Save the dictionary
        self.save(arr)

    def __contains__(self, key:V) -> bool:

        keys = self.read().keys()

        return (key in keys)
    
    def __str__(self) -> str:
        return dumps(
            obj = self.read(),
            indent = 2
        )
    
    __repr__ = __str__

#========================================================
