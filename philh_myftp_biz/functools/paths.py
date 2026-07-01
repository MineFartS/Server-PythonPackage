from traceback import FrameSummary, extract_stack
from types import FunctionType
from os.path import basename

def cpath(obj) -> str:
    """
    Class Path

    Ex: `cpath(print) -> '__builtins__.print'`
    """
    if not isinstance(obj, (type, FunctionType)):
        obj = obj.__class__

    return obj.__module__ + '.' + obj.__qualname__

def strframe(frame: FrameSummary) -> str:
    return f'{basename(frame.filename)}:{frame.lineno}'

def spath(
    x: int = 0,
    y: int = -1
) -> list[str]:
    """
    Stack Path
    Ex: `spaths() -> ['test.py:14', ...]`
    """

    stack = list(filter(
        lambda x: "<frozen " not in x.filename, 
        extract_stack()
    )) [x:y]

    return [strframe(f) for f in stack]
