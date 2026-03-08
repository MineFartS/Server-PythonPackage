from typing import Literal, TYPE_CHECKING, Callable, Any
from functools import cache, partial

if TYPE_CHECKING:
    from .db import Color

from sys import stdout, stderr # pyright: ignore[reportUnusedImport]

_cls_cmd = '8005951a000000000000008c162a2a2a20436c656172205465726d696e616c202a2a2a942e'

#========================================================

def width() -> int:
    """
    Get the # of columns in the terminal
    """
    from shutil import get_terminal_size

    return get_terminal_size().columns

def del_last_line() -> None:
    """
    Clear the previous line in the terminal
    """
    
    print(
        "\033[A{}\033[A\n".format(' ' * width()),
        end = ''
    )

#========================================================

def is_elevated() -> bool:
    """
    Check if the current execution has Administrator Access
    """
    from ctypes import windll

    try:
        return windll.shell32.IsUserAnAdmin()
    except:
        return False
    
def elevate() -> None:
    """
    Restart the current execution as Administrator
    """
    from elevate import elevate

    if not is_elevated():
        elevate()

#========================================================

def write(
    text: str,
    stream: Literal['out', 'err'] = 'out',
    flush: bool = True
) -> None:
    """
    Write text to the sys.stdout or sys.stderr buffer
    """
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
    """
    Wrapper for built-in print function
    """
    from .db import Color
    
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
    from inputimeout import inputimeout, TimeoutOccurred
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
    """
    Pause the execution and wait for user input
    """
    from os import system
    from .pc import OS

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
    from .pc import OS

    print(_cls_cmd)
    
    if OS == 'windows':
        system('cls')
    else:
        system('clear')

def warn(exc: Exception) -> None:
    """
    Print an exception to the terminal without stopping the execution
    """
    from traceback import print_exception
    from io import StringIO
    
    IO = StringIO()

    print_exception(exc, file=IO)

    write(IO.getvalue(), 'err')

#========================================================

class ProgressBar:

    class Pipe:

        def __init__(self,
            pbar: 'ProgressBar'
        ) -> None:
            self.pbar = pbar

        def write(self, s:str):
            import sys

            if self.pbar.finished:
                sys.stdout = stdout
            else:
                self.pbar.clear()

            #
            stdout.write(s)

        def flush(self):
            pass

    __bar_format = "{n_fmt}/{total_fmt} | {bar} | {elapsed}"

    def __init__(self,
        total: int = 0
    ) -> None:
        from .process import Thread
        from tqdm import tqdm
        import sys

        self._tqdm = tqdm(
            iterable = range(total),
            bar_format = self.__bar_format,
            dynamic_ncols = True
        )

        self.reset = self._tqdm.reset
        self.stop  = self._tqdm.close
        self.step  = self._tqdm.update
        self.clear = self._tqdm.clear
        self.flush = self._tqdm.refresh

        self.total: int|float = self._tqdm.total

        sys.stdout = self.Pipe(pbar=self)

        Thread(self.__refresh)

    @property
    def finished(self) -> bool:

        if self._tqdm.total == 0:
            return False
        else:
            return (self._tqdm.n == self._tqdm.total)

    @property
    def running(self):
        return not (self.finished or self._tqdm.disable)
        
    def __refresh(self):
        from time import sleep

        lastval = None

        while self.running:

            # Wait .3 seconds
            sleep(.3)
            
            # Update the timer
            self._tqdm.refresh()

            # Sync the total
            self._tqdm.total = self.total

            if lastval != self._tqdm.n:

                n = self._tqdm.n
                t = self._tqdm.total

                try:
                    p = round(n/t, 2)
                except ZeroDivisionError:
                    p = 0

                Log.VERB(f'ProgressBar: ({p}%, n={n}, t={t})')

                lastval = n

#========================================================

@cache
def Args() -> list:
    """
    Read Command Line Arguements with automatic formatting
    """
    from .text import auto_convert
    from sys import argv

    return [auto_convert(arg) for arg in argv[1:]]

class ParsedArgs:

    def __init__(self,
        name: str = 'Program Name',
        desc: str = 'What the program does',
        epilog: str = 'Text at the bottom of help'
    ) -> None:
        from argparse import ArgumentParser
        
        #
        self.__parser = ArgumentParser(
            prog = name,
            description = desc,
            epilog = epilog
        )

        self.__handlers: dict[str, Callable[[str], Any]] = {}

        self.__defaults: dict[str, Any] = {}

        self.__cache: dict[str, Any] = {}

        #
        self.Flag(
            name = 'verbose',
            letter = 'v',
            desc = 'Advanced Debugging'
        )

    def Arg(self,
        name: str,
        default: str = None,
        desc: str = None,
        handler: Callable[[str], Any] = lambda x: x
    ) -> None:
        
        self.__handlers[name] = handler

        self.__defaults[name] = default

        self.__parser.add_argument(
            '--'+name,
            default = -1,
            help = desc,
            dest = name,
        )

    def Flag(self,
        name: str,
        letter: str = None,
        desc: str = None,
        invert: bool = False
    ) -> None:
        
        flags = ['--'+name]

        if letter:
            flags.insert(0, '-'+letter)
        
        self.__parser.add_argument(
            *flags,
            help = desc,
            dest = name,
            action = 'store_true'
        )

        if invert:
            self.__handlers[name] = lambda x: not x
            self.__defaults[name] = True
        else:
            self.__handlers[name] = lambda x: x
            self.__defaults[name] = False

    def __getitem__(self,
        key: str
    ):
        
        if key in self.__cache:

            return self.__cache[key]

        else:

            parsed = self.__parser.parse_known_args()[0]
            
            handler = self.__handlers[key]

            rvalue = getattr(parsed, key)
            
            if rvalue == -1:
                
                value = self.__defaults[key]
                Log.VERB(f'Parsed Arguement: {key=} | {self.__defaults[key]=}')
            
            else:

                value = handler(rvalue)
                Log.VERB(f'Parsed Arguement: {key=} | {rvalue=} | {value=}')

            self.__cache[key] = value

            return value

#========================================================

class Log:
    """```
    VERB: 10
    INFO: 20
    MAIN: 25
    WARN: 30
    FAIL: 40
    CRIT: 50
    ```"""

    def _log(
        msg: Any,
        exc_info: Any = None,
        level: int = None
    ) -> None:
        from logging import log

        log(level, msg, exc_info=exc_info)

    VERB = partial(_log, level=10)

    INFO = partial(_log, level=20)
    
    MAIN = partial(_log, level=25)

    WARN = partial(_log, level=30)

    FAIL = partial(_log, level=40)

    CRIT = partial(_log, level=50)

#========================================================