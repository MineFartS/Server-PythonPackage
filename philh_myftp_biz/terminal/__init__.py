from typing import Literal, TYPE_CHECKING
from functools import cache

if TYPE_CHECKING:
    from ..pc.Path import Path
    from ..db import Color

from sys import stdout, stderr # pyright: ignore[reportUnusedImport]

from .ProgressBar import ProgressBar # pyright: ignore[reportUnusedImport]
from .Args import Args # pyright: ignore[reportUnusedImport]
from .KIC import KIC # pyright: ignore[reportUnusedImport]
from . import Log # pyright: ignore[reportUnusedImport]

# TODO: Temporary Backwards Compatibility
ParsedArgs = Args

_cls_cmd = '8005951a000000000000008c162a2a2a20436c656172205465726d696e616c202a2a2a942e'

#========================================================

def width() -> int:
    """Get the # of columns in the terminal"""
    from shutil import get_terminal_size

    return get_terminal_size().columns

def del_last_line() -> None:
    """Clear the previous line in the terminal"""
    
    print(
        "\033[A{}\033[A\n".format(' ' * width()),
        end = ''
    )

#========================================================

def is_elevated() -> bool:
    """Check if the current execution has Administrator Access"""
    from ctypes import windll

    try:
        return windll.shell32.IsUserAnAdmin()
    except:
        return False
    
def elevate() -> None:
    """Restart the current execution as Administrator"""
    from elevate import elevate

    if not is_elevated():
        elevate()

#========================================================

def write(
    text: str,
    stream: Literal['out', 'err'] = 'out',
    flush: bool = True
) -> None:
    """Write text to the sys.stdout or sys.stderr buffer"""
    from io import StringIO
    import sys
    
    _stream: StringIO = getattr(sys, 'std'+stream)
    
    _stream.write(text)

    if flush:
        _stream.flush()

def print(
    *args:str,
    pause: bool = False,
    color: 'Color.names' = 'DEFAULT',
    sep: str = ' ',
    end: str = '\n',
    overwrite: bool = False
) -> None:
    """Wrapper for built-in print function"""
    from ..db import Color
    
    if overwrite:
        end = ''
        del_last_line()
    
    message = Color.values[color.upper()]
    for arg in args:
        message += str(arg) + sep

    message = message[:-1] + Color.values['DEFAULT'] + end

    if pause:
        input(prompt=message)
    else:
        write(text=message)

#========================================================

def input[D] (
    prompt: str,
    timeout: int = None,
    default: D = None
) -> D | str:
    """
    Ask for user input from the terminal

    Will return default upon timeout
    """
    from .inputimeout import inputimeout, TimeoutOccurred
    from builtins import input

    if timeout:

        try:
            return inputimeout(
                prompt = prompt,
                timeout = timeout
            )
        except TimeoutOccurred:
            return default
    
    else:
        return input(prompt)

def pause() -> None:
    """Pause the execution and wait for user input"""
    from os import system
    from ..pc import OS

    if OS == 'windows':
        system('pause')
    else:
        system('read -n 1 -r -s -p "Press any key to continue . . ."')

#========================================================

def dash(p:int=100) -> None:
    """
    Print dashes to the terminal

    (p is the % of the terminal width)

    Ex: dash(50) -> |-------------             |

    """
    
    print(width() * (p//100) * '-')

def cls() -> None:
    """
    Clear the terminal window

    (Prints a hexidecimal value so it can be detected from a subprocess)
    """
    from os import system
    from ..pc import OS

    print(_cls_cmd)
    
    if OS == 'windows':
        system('cls')
    else:
        system('clear')

def warn(exc: Exception) -> None:
    """Print an exception to the terminal without stopping the execution"""
    from traceback import print_exception
    from io import StringIO
    
    IO = StringIO()

    print_exception(exc, file=IO)

    write(IO.getvalue(), 'err')

#========================================================

@cache
def main_module():
    from sys import modules

    try:
        
        modules['__main__'].__file__

        return modules['__main__']

    except AttributeError:

        from _frozen_importlib import _module_locks

        fullname: str = next(iter(_module_locks))

        name = fullname.split('.')[0]

        return modules[name]

def set_package(path:str|Path):
    from ..pc.Path import Path
    import sys

    path = Path(path)
    sys.path.insert(0, str(path.parent))
    main_module().__package__ = path.name

@cache
def script_file():
    from ..pc import Path

    return Path(main_module().__file__)

#========================================================
