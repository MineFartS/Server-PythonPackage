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

def spath(
    x: int = 0,
    y: int = -1
) -> list[str]:
    """
    Stack Path
    Ex: `spaths() -> ['test.py:14', ...]`
    """

    return [
        f'{basename(frame.filename)}:{frame.lineno}' for frame in extract_stack()
        if "<frozen " not in frame.filename # Frozen imports
        and "\\Lib\\runpy.py" not in frame.filename # VS Code Debugging
        and "\\Lib\\importlib\\util.py" not in frame.filename # VS Code Debugging
        and "\\.vscode\\extensions\\" not in frame.filename # VS Code Debugging
        and not (("\\functools.py" in frame.filename) and (frame.lineno == 1126)) # Cached Property
    ] [x:y]
