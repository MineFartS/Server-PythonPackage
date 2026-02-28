from typing import TYPE_CHECKING, Any, Generator

if TYPE_CHECKING:
    from .db import Color

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

        #========================================================
        # PRIVATE

        self.private = False

        if self.name.startswith('__'):
            self.private = True
        
        elif hasattr(self.parent, '__name__') and (self.name.startswith(f'_{self.parent.__name__}__')):
            self.private = True
        
        elif (self.name.startswith(f'_{self.parent.__class__.__name__}__')):
            self.private = True

        else:
            
            for base in self.parent.__class__.__bases__:

                if self.name.startswith(f'_{base.__name__}__'):
                
                    self.private = True
                    break

        #========================================================
        # VALUE

        if self.private:
            self.value = None
        else:
            self.value = getattr(self.parent, self.name)

        #========================================================
        # CALLABLE

        self.callable = callable(self.value)

        #========================================================

    def __str__(self):
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
        except:
            return str(self.value)

#========================================================

def attrs(obj:Any) -> Generator[attr, Any, None]:
    """
    Get all attributes of an instance or object
    """

    for name in dir(obj):

        yield attr(parent=obj, name=name)

def path(obj:Any) -> str:
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
    IO.write(path(obj))
    IO.write(f' @{loc(obj)}')
    IO.write(' ---\n')

    for c in attrs(obj):
        if not (c.private or c.callable or (c.value is None)):
            IO.write(c.name)
            IO.write(' = ')
            IO.write(str(c))
            IO.write('\n')

    return IO.getvalue()

def log(
    obj: Any,
    color: 'Color.names' = 'DEFAULT'
) -> None:
    """
    Print all attributes of the instance to the terminal
    """
    from .terminal import print as __print
    
    #========================
    # PRINT

    print()

    __print(
        stringify(obj),
        color = color
    )

    print()

#========================================================

def dictify(obj:Any) -> dict:
    """
    Convert an instance to a dictionary
    """

    json_obj: dict[str, Any] = {}

    for c in attrs(obj):

        if not (c.private or c.callable):
        
            json_obj[c.name] = c.value

    return json_obj

#========================================================

class EventListener:

    def __init__(self) -> None:
        
        self.events = []

        self.__iadd__ = self.events.append

        self.add = self.events.append

        self.running: bool = False

    def __iter__(self):

        self.running = True
        
        return self

    def __next__(self):

        if not self.running:
            raise StopIteration()

        while len(self.events) == 0:
            pass

        event = self.events[0]

        del self.events[0]

        return event
