from typing import TYPE_CHECKING, Self, Generator, Any, Callable
from json import load, loads, dump, dumps

if TYPE_CHECKING:
    from .file import JSON, PKL, YAML, TOML, INI
    from .pc import _var

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

    def __init__(self,
        t: 'dict[str, V] | Self[V] | Any' = {}
    ):
        from .file import PKL, temp
        from .classOBJ import path

        if isinstance(t, Dict):
            self.var = t.var

        elif hasattr(t, 'read') and hasattr(t, 'save'):
            self.var = t

        elif isinstance(t, dict):
            self.var = PKL(
                path = temp('table', 'json'),
                default = t
            )

        else:
            raise TypeError(path(t))
        
        self.read: Callable[[], dict[str, V]] = self.var.read
        """Read Data"""

        self.save: Callable[[dict[V]], None] = self.var.save
        """Save Data"""

    def items(self) -> Generator[list[str, V]]:
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
        dict: dict[str, V]
    ) -> Self[V]:
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