from typing import Literal, TYPE_CHECKING, Callable, Any
from sys import stdout, stderr

if TYPE_CHECKING:
    from .db import Color
    from .pc import Path
    from logging import LogRecord

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
    text,
    stream: Literal['out', 'err'] = 'out',
    flush: bool = True
) -> None:
    """
    Write text to the sys.stdout or sys.stderr buffer
    """
    from io import StringIO
    import sys
    
    stream: StringIO = getattr(sys, 'std'+stream)
    
    stream.write(text)

    if flush:
        stream.flush()

def print(
    *args,
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
        input(message)
    else:
        write(message)

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

def pause():
    """
    Pause the execution and wait for user input
    """
    from os import system
    from .pc import OS

    if OS == 'windows':
        system('pause')
    else:
        pass # TODO

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

    (Prints a hexidecimal value so the philh.myftp.biz.run can send the signal up from a subprocess)
    """
    from .text import hex
    from os import system
    from .pc import OS

    print(hex.encode('*** Clear Terminal ***'))
    
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
        ):
            self.pbar = pbar

        def write(self, s:str):
            import sys

            if self.pbar.finished():
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
    ):
        from .process import thread
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

        self.total = self._tqdm.total

        sys.stdout = self.Pipe(pbar=self)

        thread(self.__refresh)

    def finished(self) -> bool:

        if self._tqdm.total == 0:
            return False
        else:
            return (self._tqdm.n == self._tqdm.total)

    def running(self):
        return not (self.finished() or self._tqdm.disable)
        
    def __refresh(self):
        from time import sleep

        lastval = None

        while self.running():

            # Wait .3 seconds
            sleep(.3)
            
            # Update the timer
            self._tqdm.refresh()

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

def Args() -> list:
    """
    Read Command Line Arguements with automatic formatting
    """
    from .array import auto_convert
    from sys import argv

    return auto_convert(argv[1:])

class ParsedArgs:

    def __init__(self,
        name: str = 'Program Name',
        desc: str = 'What the program does',
        epilog: str = 'Text at the bottom of help'
    ):
        from argparse import ArgumentParser
        
        #
        self.__parser = ArgumentParser(
            prog = name,
            description = desc,
            epilog = epilog
        )

        self.__handlers: dict[str, Callable[[str], Any]] = {}

        self.__defaults: dict[str, Any] = {}

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
        handler: None | Callable[[str], Any] = None
    ):
        
        if handler:
            self.__handlers[name] = handler
        else:
            self.__handlers[name] = lambda x: x

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
    ):
        
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

        parsed = self.__parser.parse_known_args()[0]
        
        handler = self.__handlers[key]

        rvalue = getattr(parsed, key)
        
        if rvalue == -1:
            
            value = self.__defaults[key]
            Log.VERB(f'Parsed Arguement: {key=} | {self.__defaults[key]=}')
        
        else:

            value = handler(rvalue)
            Log.VERB(f'Parsed Arguement: {key=} | {rvalue=} | {value=}')

        return value

#========================================================

class Log:

    #========================================================
    # WRITERS

    from logging import debug    as VERB
    from logging import info     as INFO
    from logging import warning  as WARN
    from logging import error    as FAIL
    from logging import critical as CRIT

    #========================================================

    def file(path: 'Path'):
        from logging import FileHandler, DEBUG

        # Create a FileHandler
        fh = FileHandler(str(path))
        fh.setLevel(DEBUG) # Log all messages to the file
        fh.setFormatter(Log.FORMATTER)

    #========================================================