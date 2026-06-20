from json import dumps

class Collection[T, STRUCT]:

    _default: T

    _cache: None|STRUCT

    def __init__(self,
        t: STRUCT = None
    ) -> None:
        from types import GeneratorType
        from ..file import PKL, temp

        if isinstance(t, Collection):
            self.var = t.var            

        elif hasattr(t, 'read') and hasattr(t, 'save'):
            self.var = t

        else:

            if isinstance(t, (tuple, filter, GeneratorType)):
                t = list(t)

            self.var = PKL(
                path = temp('Collection', 'pkl')
            )
            self.var.save(t)

        self.var.default = self._default

    def read(self) -> STRUCT:

        if not hasattr(self, '_cache'):
            self._cache = self.var.read()

        return self._cache # pyright: ignore[reportReturnType]
    
    def save(self, data:STRUCT) -> None:

        self._cache = data

        self.var.save(data)
    
    def __len__(self) -> int:
        return len(self.read())
        
    def __setitem__(self, key, value:T) -> None:

        # Get the raw dictionary
        data: STRUCT = self.read()

        # Update the key with the value
        data[key] = value

        # Save the raw dictionary
        self.save(data)

    def __delitem__(self, key) -> None:
        
        # Get the raw dictionary
        data: STRUCT = self.read()
        
        # Remove the key
        del data[key]
        
        # Save the dictionary
        self.save(data)

    def __contains__(self, key) -> bool:
        return (key in self.read())
    
    def __str__(self) -> str:
        return dumps(
            obj = self.read(),
            indent = 2
        )
    
    __repr__ = __str__
