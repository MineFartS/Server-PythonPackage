from typing import TYPE_CHECKING, Self, Generator
from json import load, loads, dump, dumps

if TYPE_CHECKING:
    from .file import JSON, PKL, YAML, TOML, INI
    from .pc import _var

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

class InvalidDictError(Exception):
    pass

class Dict[V]:
    """
    Dict/Json Wrapper

    Stores data to the local disk instead of memory
    """

    def __init__(self,
        table: 'dict[str, V] | Self[str, V] | JSON | _var | PKL | YAML | TOML | INI' = {}
    ):
        from .file import JSON, PKL, YAML, TOML, INI, temp
        from .classOBJ import path
        from .pc import _var

        if isinstance(table, (JSON, _var, PKL, YAML, TOML, INI)):
            self.var = table

        elif isinstance(table, Dict):
            self.var = table.var

        elif isinstance(table, dict):
            self.var = PKL(
                path = temp('table', 'json')
            )
            self.var.save(table)

        else:

            raise InvalidDictError(path(table))

    def items(self) -> Generator[list[str, V]]:
        return self.read().items()

    def save(self, data:dict[str, V]) -> None:
        """Save Data"""
        self.var.save(data)

    def read(self) -> dict[str, V]:
        """Read Data"""
        return self.var.read()
    
    def __iter__(self):
        return iter(self.read())

    def __len__(self) -> int:
        return len(self.keys())
    
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

    remove = __delitem__

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
        return dumps(self.read(), indent=2)

