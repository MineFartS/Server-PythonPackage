from typing import TYPE_CHECKING, Any, Generator, Callable

if TYPE_CHECKING:
    from .db import Color

#========================================================

class attr:
    """
    Attribute of Instance/Object
    """

    private: bool

    value: Any

    callable: bool

    null: bool

    parent: Any

    name: str

    def __init__(self,
        parent: Any,
        name: str
    ) -> None:
        self.name: str = name
        self.parent = parent

    def __getattr__(self, name:str):
        
        match name:

            case 'name':
                return self.__dict__['name']
            
            case 'parent':
                return self.__dict__['parent']

            case 'private':

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
            
            case 'value':

                if not self.private:

                    try:
                        return getattr(self.parent, self.name)
                    except:
                        pass

            case 'callable':
                return callable(self.value)
            
            case 'null':
                return (self.value is None)
            
            case _:
                raise AttributeError(f"type object '{path(self)}' has no attribute '{name}'")

    def __str__(self) -> str:
        """
        Get the value of the attribute as a string

        Formats with json.dumps
        """
        from .json import dumps, StringEncoder

        try:
            return dumps(
                obj = self.value,
                indent = 2,
                cls = StringEncoder
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

        if not (c.private or c.callable or c.null):

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


def initPartialClass(
    super: Any,
    self: Any,
    key: str,
    value: Any
) -> None:
    """

    #### Copies all methods from parent class and replaces the child method with a partial function

    ### EXAMPLE:
    ```
    class Parent:
    
        def __init__(self):
            pass
            
        def test_1(self, hi:str):
            return f'{hi} world'

        def test_2(self):
            return 'hello world'

    class Child(Parent):
    
        def __init__(self):
            
            initPartialClass(
                super = Parent,
                self = self,
                key = 'hi',
                value = 'hello'
            )

    >>> p = Parent()

    >>> p.test_1()
    TypeError: test_1() missing 1 required positional argument: 'hi'

    >>> p.test_1('hello')
    'hello world'

    >>> c = Child()
    
    >>> c.test_1()
    'hello world'

    >>> c.test_1('hi')
    'hi world'
    ```
    """
    from inspect import signature
    from functools import partial

    for _key, _value in vars(super).items():

        _params: list[str] = signature(value).parameters
        
        CALLABLE: bool = callable(value)

        PUBLIC: bool = ('_' not in _key)

        HASKEY: bool = (CALLABLE and (_key in _params))

        if CALLABLE and PUBLIC and HASKEY:

            setattr(
                obj = self,
                name = _key,
                value = partial(
                    func = _value, 
                    self = self,
                    **{key: value}
                )
            )