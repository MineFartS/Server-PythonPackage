from inspect import signature
from functools import wraps

def force_in_types(func):
    """
    Forces parameter types
    
    EXAMPLE:
    ```
    @force_in_types
    def myfunc(x: int, y: float):
        ...
    
    myfunc('1', '2') -> myfunc(int('1'), float('2'))
    myfunc(3, '4') -> myfunc(3, float('4'))
    """

    @wraps(func)
    def wrapper(*args, **kwargs):

        # Bind and apply defaults to arguments
        bargs = signature(func).bind(*args, **kwargs)
        bargs.apply_defaults()

        # Coerce input parameter types
        for name, value in bargs.arguments.items():
            etype = func.__annotations__.get(name)
            if etype and not isinstance(value, etype):
                bargs.arguments[name] = etype(value)

        # Execute the function with coerced arguments
        return func(*bargs.args, **bargs.kwargs)
    
    return wrapper

def force_out_type(func):
    """
    Forces return type
    
    EXAMPLE:
    ```
    @force_out_type
    def myfunc(x: int, y: float) -> list:
        yield x
        yield y

    myfunc(1, 2) -> [1, 2]
    """

    @wraps(func)
    def wrapper(*args, **kwargs):

        # Bind and apply defaults to arguments
        bargs = signature(func).bind(*args, **kwargs)
        bargs.apply_defaults()

        # Execute the function
        result = func(*bargs.args, **bargs.kwargs)

        # Coerce the return type if annotated
        return_type = func.__annotations__.get('return')
        if return_type and not isinstance(result, return_type):
            return return_type(result)

        return result
    
    return wrapper


