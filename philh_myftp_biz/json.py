from json import load, loads, dump, dumps
from typing import Any, ItemsView

#========================================================

def valid(value:str):
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
    Dict/Json Wrapper

    Stores data to the local disk instead of memory
    """

    type RAW = dict[str, V]
    type OUT = Dict[V]

    def __init__(self,
        t: RAW|OUT|Any = {}
    ):
        from .file import PKL, temp
        from .classOBJ import path

        if isinstance(t, Dict):
            self._var = t._var

        elif hasattr(t, 'read') and hasattr(t, 'save'):
            self._var = t

        elif isinstance(t, dict):
            self._var = PKL(
                path = temp('table', 'json'),
                default = t
            )

        else:
            raise TypeError(path(t))

    def read(self) -> RAW:
        """Read Data"""
        return self._var.read()
    
    def save(self, data:RAW) -> None:
        """Save Data"""
        return self._var.save(data)

    def items(self) -> ItemsView[str, V]:
        return self.read().items()
    
    def __iter__(self):
        return iter(self.read())

    def __len__(self) -> int:
        return len(self.read().keys())
    
    def __getitem__(self, key) -> None | V:
        try:
            return self.read()[key]
        except KeyError:
            return None

    def __setitem__(self,
        key: str,
        value: V
    ) -> None:

        # Get the raw dictionary
        data = self.read()

        # Update the key with the value
        data[key] = value

        # Save the raw dictionary
        self.save(data)

    def __delitem__(self, key:str) -> None:
        
        # Get the raw dictionary
        arr = self.read()
        
        # Remove the key
        del arr[key]
        
        # Save the dictionary
        self.save(arr)

    def __contains__(self, value:V):
        return (value in self.read())
    
    def __iadd__(self,
        dict: RAW
    ) -> OUT:
        """
        Append another dictionary
        """

        # Get the raw dictionary
        data = self.read()
        
        # Iter through all keys
        for name in dict:
            
            # Set the key to the value of the input dictionary
            data[name] = dict[name]
        
        # Save the data
        self.save(data)

        return self

    def __str__(self) -> str:
        return dumps(
            obj = self.read(),
            indent = 2
        )

#========================================================