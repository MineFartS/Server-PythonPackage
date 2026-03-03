from typing import Any, Generator, Callable

#========================================================

class attr:
    """
    Attribute of Instance/Object
    """

    def __init__(self,
        parent: Any,
        name: str
    ) -> None:
        self.name: str = name
        self.parent = parent

    @property
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

    @property
    def value(self):
        
        if not self.private:

            try:
                return getattr(self.parent, self.name)
            except:
                pass

    @property
    def callable(self):
        return callable(self.value)
    
    @property
    def null(self):
        return (self.value is None)

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

def attrs(obj:Any) -> Generator[attr, Any, None]:
    """
    Get all attributes of an instance or object
    """

    for name in dir(obj):

        yield attr(parent=obj, name=name)

def cpath(obj:Any) -> str:
    """
    Get Full path of instance

    Ex: path(print) -> '__builtins__.print'
    """

    return obj.__class__.__module__ + '.' + obj.__class__.__qualname__

def loc(obj:Any) -> str:
    """
    Get the hexadecimal location of an instance in memory
    """
    return hex(id(obj))

#========================================================

def stringify(obj:Any) -> str:
    """
    Creates a string containing a table of all attributes of an instance
    (for debugging)
    """
    from io import StringIO
    
    IO = StringIO()

    IO.write('--- ')
    IO.write(cpath(obj))
    IO.write(f' @{loc(obj)}')
    IO.write(' ---\n')

    for c in attrs(obj):

        if not (c.private or c.callable or c.null):

            IO.write(c.name)
            IO.write(' = ')
            IO.write(str(c))
            IO.write('\n')

    return IO.getvalue()

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
