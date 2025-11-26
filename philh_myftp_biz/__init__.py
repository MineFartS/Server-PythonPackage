from typing import Literal, TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .file import PKL
    from .db import Ring
    from .pc import Path
    from threading import Thread

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
        
        self.__parser = ArgumentParser(
            prog = name,
            description = desc,
            epilog = epilog
        )

    def __id(self, name:str):
        from .text import hex

        return '_'+hex.encode(name)

    def parse(self,
        name: str,
        default = None,
        desc: str = None
    ):

        self.__parser.add_argument(
            '--'+name,
            default = default,
            help = desc,
            dest = self.__id(name)
        )

    def __getitem__(self,
        key: str
    ):
        from .text import auto_convert

        obj = self.__parser.parse_args()
        name = self.__id(key)
        
        value = getattr(obj, name)

        return auto_convert(value)

def var(
    title: str,
    default = '',
    type: Literal['temp', 'keyring'] = 'temp'
    ) -> 'PKL | Ring':
    """
    Quick Local Variable Builder

    pkl -> philh_myftp_biz.file.PKL
    ring -> philh_myftp_biz.db.Ring
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

def thread(func,
    *args,
    **kwargs
) -> 'Thread':
    """
    Quickly Start a Thread
    """
    from threading import Thread

    p = Thread(
        target = func,
        kwargs = kwargs,
        args = args
    )

    p.start()
    
    return p

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
        cores: int = 4,
        timeout: int | None = None,
        autostart: bool = True
    ):
        from .array import List, stringify
        from .pc import Path, cwd
        from sys import executable

        # =====================================

        self.__wait = wait
        self.__hide = hide
        self.__file = Path(args[0])
        self.__cores = List([0, 1, 2, 3]).shuffled()[:cores]
        self.__timeout = timeout

        if dir:
            self.__dir = dir
        else:
            self.__dir = cwd()
        
        # =====================================   

        if isinstance(args, (tuple, list)):
            args = stringify(args)
        else:
            args = [args]

        if terminal == 'ext':

            exts = {
                'ps1' : 'psfile',
                'py'  : 'py',
                'exe' : 'cmd',
                'bat' : 'cmd',
                'vbs' : 'vbs'
            }

            ext = self.__file.ext()

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

        if autostart:
            self.start()

    def __background(self) -> None:
        """
        Background Tasks
        """
        from .time import sleep

        while True:
            
            sleep(.1)

            if self.finished() or self.timed_out():
                self.stop()
                return
            
            else:
                self.__task.cores(*self.__cores)

    def __stdout(self) -> None:
        """
        Output Manager
        """
        from .text import hex
        from .pc import cls, terminal

        cls_cmd = hex.encode('*** Clear Terminal ***')

        for line in self.__process.stdout:
            
            if cls_cmd in line:
                cls()

            elif len(line) > 0:

                self.__output += line

                if not self.__hide:
                    terminal.write(line, 'out')

    def __stderr(self) -> None:
        """
        Error Manager
        """
        from .pc import terminal

        for line in self.__process.stderr:

            self.__output += line

            terminal.write(line, 'err')

    def start(self) -> None:
        """
        Start the subprocess
        """
        from subprocess import Popen, PIPE
        from .time import Stopwatch
        from .pc import Task
       
        self.__process = Popen(
            args = self.__args,
            cwd = self.__dir.path,
            stdout = PIPE,
            stderr = PIPE,
            text = True,
            bufsize = 1
        )

        self.__task = Task(self.__process.pid)
        self.__stopwatch = Stopwatch().start()

        self.__output = ''

        self.wait = self.__process.wait

        thread(self.__stdout)
        thread(self.__stderr)
        thread(self.__background)

        if self.__wait:
            self.wait()

    def finished(self) -> bool:
        """
        Check if the subprocess is finished
        """
        return (not self.__task.exists())

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
        if self.__timeout:
            return (self.__stopwatch.elapsed() >= self.__timeout)

    def stop(self) -> None:
        """
        Stop the Subprocess
        """
        self.__task.stop()
        self.__stopwatch.stop()

    def output(self,
        format: Literal['json', 'hex'] = None
    ) -> 'str | dict | list | bool | Any':
        """
        Read the output from the Subprocess
        """
        from . import json
        from .text import hex

        if format == 'json':
            return json.loads(self.__output.strip())
        
        elif format == 'hex':
            return hex.decode(self.__output.strip())
        
        else:
            return self.__output.strip()