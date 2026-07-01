def cpath(obj) -> str:
    """
    Class Path

    Ex: `cpath(print) -> '__builtins__.print'`
    """
    from types import FunctionType

    if not isinstance(obj, (type, FunctionType)):
        obj = obj.__class__

    return obj.__module__ + '.' + obj.__qualname__

def spath(x:int) -> str:
    """
    Stack Path

    Ex: `spath(0) -> 'test.py:14'`
    """
    from traceback import extract_stack
    from os import path

    stack = filter(
        lambda x: "<frozen " not in x.filename, 
        extract_stack()
    )

    frame = list(stack)[x]

    return f'{path.basename(frame.filename)}:{frame.lineno}'