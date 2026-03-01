from typing import Literal, TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from .pc import Path

#========================================================

class Thread:
    """
    Quickly Start a Thread
    """

    def __init__(self,
        func: Callable,
        *args: str,
        **kwargs: str
    ) -> None:
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

class Sleeper:
    """
    Call a function before exiting after main thread has ended
    """

    def __init__(self,
        func: Callable,
        *args: str,
        **kwargs: str
    ) -> None:
        from threading import Thread

        self.func = func
        self.args = args
        self.kwargs = kwargs

        # Create new thread
        Thread(self._main).start()

    def _main(self) -> None:
        from time import sleep

        while Alive():
            sleep(.1)

        self.func(*self.args, **self.kwargs)

def Alive() -> bool:
    """
    Check if the main thread is running
    """
    from threading import main_thread

    return main_thread().is_alive()

#========================================================

class SubProcess:
    """
    Subprocess Wrapper
    """

    _hide: bool
    _wait: bool

    def __init__(self,
        args: list|tuple|str,
        terminal: None|Literal['cmd', 'ps', 'psfile', 'py', 'pym', 'vbs'] = 'cmd',
        dir: 'Path|None' = None
    ) -> None:
        from subprocess import Popen, PIPE
        from .array import stringify
        from sys import executable
        from .pc import Path, cwd

        # =====================================

        if dir is None:
            dir = cwd()
                    
        # =====================================

        if isinstance(args, (tuple, list)):
            args = stringify(args)
        else:
            args = [args]

        if terminal is None:

            match Path(args[0]).ext():

                case 'ps1': terminal='psfile'

                case 'py': terminal='py'

                case 'exe': terminal='cmd'

                case 'bat': terminal='cmd'

                case 'vbs': terminal='vbs'

                case _: terminal='cmd'

        match terminal:

            case 'cmd':
                args = ['cmd', '/c', *args]

            case 'ps':
                args = ['Powershell', '-Command', *args]

            case 'psfile':
                args = ['Powershell', '-File', *args]

            case 'py':
                args = [executable, *args]

            case 'pym':
                args = [executable, '-m', *args]
        
            case 'vbs':
                args = ['wscript', *args]

        # =====================================

        self._process = Popen(
            args = args,
            cwd = str(dir),
            stdout = PIPE,
            stderr = PIPE,
            text = True,
            errors = 'ignore'
        )

        self._task = SysTask(self._process.pid)

        self.wait = self._process.wait

        self.running = self._task.exists

        self.stop = self._task.stop

        # =====================================

        self.stdout  = ''
        self.stderr  = ''
        self.stdcomb = ''

        # Start Status Monitor
        Thread(self.__monitor)

        # =====================================

        # Wait for process to complete if required
        if self._wait:
            self.wait()

    def __monitor(self) -> None:
        from .terminal import _cls_cmd, cls, write

        stdout = iter(self._process.stdout)
        stderr = iter(self._process.stderr)

        while self.running() and Alive():

            outline = next(stdout, '')

            if _cls_cmd in outline:

                # Reset stream buffers
                self.stdout = ''
                self.stderr = ''
                self.stdcomb = ''

                #
                if not self._hide:
                    cls()

            elif len(outline) > 0:

                #
                self.stdout += outline
                self.stdcomb += outline

                #
                if not self._hide:
                    write(outline, 'out')

            errline = next(stderr, None)

            if errline:

                self.stderr += errline
                self.stdcomb += errline

                if not self._hide:
                    write(errline, 'err')

        #
        self.stop()

    def finished(self) -> bool:
        """
        Check if the subprocess is finished
        """
        return (not self.running())

    def output(self,
        format: Literal['json', 'hex'] = None,
        stream: Literal['out', 'err', 'comb'] = 'out'
    ) -> 'str | dict | list | bool | Any':
        """
        Read the output from the Subprocess
        """
        from .text import hex
        from . import json

        _stream: str = getattr(self, 'std'+stream)

        output = _stream.encode().strip()

        if format == 'json':
            return json.loads(output)
        
        elif format == 'hex':
            return hex.decode(output)
        
        else:
            return output.decode()

class Run(SubProcess):
    _hide = False
    _wait = True

class RunHidden(SubProcess):
    _hide = True
    _wait = True

class Start(SubProcess):
    _hide = False
    _wait = False

class StartHidden(SubProcess):
    _hide = True
    _wait = False

#========================================================

class SysTask:
    """
    System Task

    Wrapper for psutil.Process
    """

    def __init__(self, id:str|int) -> None:

        self.id: str | int = id
        """PID / IM"""

    def __iter__(self):
        from psutil import process_iter, Process, NoSuchProcess
        
        main = None

        if isinstance(self.id, int):

            try:
                main = Process(self.id)
            
            except NoSuchProcess:
                pass

        else:

            for proc in process_iter():
            
                if proc.name().lower() == self.id.lower():
            
                    main = Process(pid=proc.pid)
            
                    break


        if main:

            processes = [main]

            try:

                for child in main.children(recursive=True):
                
                    processes += [child]

            except NoSuchProcess:
                pass
        
        else:

            processes = []

        return iter(filter(
            lambda p: p.is_running(),    
            reversed(processes)
        ))

    def stop(self) -> None:
        """
        Stop Process and all of it's children
        """

        for p in self:
            
            p.terminate()

    def exists(self) -> bool:
        """
        Check if the process is running
        """        
        return len(list(self)) > 0
    
    def PIDs(self):
        
        for process in self:

            yield process.pid

#========================================================