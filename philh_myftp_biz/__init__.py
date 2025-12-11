from typing import Literal, TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from threading import Thread
    from .file import PKL
    from .db import Ring
    from .pc import Path

def Args() -> list:
    """
    Read Command Line Arguements with automatic formatting
    """
    from sys import argv
    from .array import auto_convert

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

        parsed, _ = self.__parser.parse_known_args()
        
        handler = self.__handlers[key]
        
        value = getattr(parsed, key)

        if value == -1:

            return self.__defaults[key]
        
        else:

            return handler(value)            
        
def var(
    title: str,
    default = '',
    type: Literal['temp', 'ring'] = 'temp'
    ) -> 'PKL | Ring':
    """
    Quick Local Variable Builder

    temp -> .file.PKL()
    ring -> .db.Key()
    """
    from .file import temp, PKL
    from .db import Ring

    if type == 'temp':

        return PKL(
            path = temp('var', 'pkl', title),
            default = default
        )

    elif type == 'keyring':
        
        ring = Ring('__variables__')
        
        return ring.Key(
            name = title,
            default = default
        )

class thread:
    """
    Quickly Start a Thread
    """

    def __init__(self,
        func: Callable,
        *args,
        **kwargs
    ) -> 'Thread':
        from threading import Thread

        # Create new thread
        self._t = Thread(
            target = func,
            kwargs = kwargs,
            args = args
        )

        # Close when main execution ends
        self._t.daemon = True

        # start the thread
        self._t.start()

        self.wait = self._t.join

        self.running = self._t.is_alive

class run:
    """
    Subprocess Wrapper
    """

    def __init__(self,
        args: list,
        wait: bool = False,
        terminal: Literal['cmd', 'ps', 'psfile', 'py', 'pym', 'vbs'] | None = 'cmd',
        dir: 'Path' = None,
        hide: bool = False,
        timeout: int | None = None,
        venv: Path = None
    ):
        from .array import stringify
        from .pc import Path, cwd
        from sys import executable

        # =====================================

        self.__wait = wait
        self.__hide = hide
        self.__timeout = timeout

        if dir:
            self.__dir = dir
        else:
            self.__dir = cwd()
        
        # =====================================   

        if isinstance(args, (tuple, list)):
            args = stringify(args)
        else:
            args = [str(args)]

        if venv:
            executable = str(venv.child('/Scripts/python.exe'))

        if terminal == 'ext':

            exts = {
                'ps1' : 'psfile',
                'py'  : 'py',
                'exe' : 'cmd',
                'bat' : 'cmd',
                'vbs' : 'vbs'
            }

            ext = Path(args[0]).ext()

            if ext:
                terminal = exts[ext]

        if terminal == 'cmd':
            self.__args = ['cmd', '/c', *args]

        elif terminal == 'ps':
            self.__args = ['Powershell', '-Command', *args]

        elif terminal == 'psfile':
            self.__args = ['Powershell', '-File', *args]

        elif terminal == 'py':
            self.__args = [executable, *args]

        elif terminal == 'pym':
            self.__args = [executable, '-m', *args]
        
        elif terminal == 'vbs':
            self.__args = ['wscript', *args]

        else:
            self.__args = args

        # =====================================

        # Start the process
        self.start()

    def __monitor(self) -> None:
        """
        Monitor the Process' status
        """
        from .time import sleep

        while True:
            
            sleep(.1)

            if self.finished() or self.timed_out():
                
                self.stop()
                
                return

    def __stdout(self) -> None:
        """
        Output Manager
        """
        from .text import hex
        from .pc import cls, terminal

        self.stdout = ''

        cls_cmd = hex.encode('*** Clear Terminal ***')

        for line in self.__process.stdout:
            
            if cls_cmd in line:

                #
                self.stdout = ''

                #
                self.stdcomb = ''
                
                #
                if not self.__hide:
                    cls()

            elif len(line) > 0:

                #
                self.stdout += line

                self.stdcomb += line

                #
                if not self.__hide:
                    terminal.write(line, 'out')

    def __stderr(self) -> None:
        """
        Error Manager
        """
        from .pc import terminal

        self.stderr = ''

        for line in self.__process.stderr:

            self.stderr += line

            self.stdcomb += line

            if not self.__hide:
                terminal.write(line, 'err')

    def start(self) -> None:
        """
        Start the subprocess
        """
        from subprocess import Popen, PIPE
        from .time import Stopwatch
        from .pc import Task
       
        #
        self.__process = Popen(
            args = self.__args,
            cwd = self.__dir.path,
            stdout = PIPE,
            stderr = PIPE,
            text = True,
            bufsize = 1,
            errors = 'ignore'
        )

        self.wait = self.__process.wait

        self.__task = Task(self.__process.pid)
        """Process Task"""
        self.PIDs = self.__task.PIDs

        self.__stopwatch = Stopwatch()
        """Process Runtime"""
        self.__stopwatch.start()

        self.stdcomb = ''

        # Start Output Manager
        thread(self.__stdout)

        # Start Error Manager
        thread(self.__stderr)

        # Start Status Monitor
        thread(self.__monitor)

        # Wait for process to complete if required
        if self.__wait:
            self.wait()

    def finished(self) -> bool:
        """
        Check if the subprocess is finished
        """
        return (not self.__task.exists())
    
    def running(self) -> bool:
        """
        Check if the subprocess is still running
        """
        return self.__task.exists()

    def restart(self) -> None:
        """
        Restart the Subprocess
        """
        self.stop()
        self.start()

    def timed_out(self) -> bool | None:
        """
        Check if the Subprocess timed out
        """

        # If a timeout value was given
        if self.__timeout:

            # Return whether the runtime exceeds the timeout
            return (self.__stopwatch.elapsed() >= self.__timeout)

    def stop(self) -> None:
        """
        Stop the Subprocess
        """

        # Kill the process and its children
        self.__task.stop()

        # Pause the runtime stopwatch
        self.__stopwatch.stop()

    def output(self,
        format: Literal['json', 'hex'] = None,
        stream: Literal['out', 'err', 'comb'] = 'comb'
    ) -> 'str | dict | list | bool | Any':
        """
        Read the output from the Subprocess
        """
        from . import json
        from .text import hex

        stream: str = getattr(self, 'std'+stream)

        output = stream.encode().strip()

        if format == 'json':
            return json.loads(output)
        
        elif format == 'hex':
            return hex.decode(output)
        
        else:
            return output