from typing import Literal, TYPE_CHECKING, Any, Callable, Generator

if TYPE_CHECKING:
    from threading import Thread
    from psutil import Process
    from .pc import Path

#========================================================

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

#========================================================

class SubProcess:
    """
    Subprocess Wrapper
    """

    _hide: bool

    _wait: bool

    def __init__(self,
        args: list,
        terminal: Literal['cmd', 'ps', 'psfile', 'py', 'pym', 'vbs', 'ext'] | None = 'cmd',
        dir: 'Path' = None,
        timeout: int | None = None
    ):
        from .array import stringify
        from .pc import Path, cwd
        from sys import executable

        # =====================================

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

    def _monitor(self) -> None:
        """
        Monitor the Process' status
        """
        from threading import main_thread
        from .time import sleep

        mt = main_thread()

        while True:
            
            sleep(.1)

            # If the either the main exec or the subprocess is stopped 
            if self.finished() or self.timed_out() or (not mt.is_alive()):
                
                self.stop()
                
                return

    def _stdout(self) -> None:
        """
        Output Manager
        """
        from .terminal import cls, write
        from .text import hex

        self.stdout = ''

        cls_cmd = hex.encode('*** Clear Terminal ***')

        for line in self._process.stdout:
            
            if cls_cmd in line:

                # Reset stdout stream
                self.stdout = ''

                # Reset stderr stream
                self.stderr = ''

                # Reset combined stream
                self.stdcomb = ''

                #
                if not self._hide:
                    cls()

            elif len(line) > 0:

                #
                self.stdout += line

                self.stdcomb += line

                #
                if not self._hide:
                    write(line, 'out')

    def _stderr(self) -> None:
        """
        Error Manager
        """
        from .terminal import write

        self.stderr = ''

        for line in self._process.stderr:

            self.stderr += line

            self.stdcomb += line

            if not self._hide:
                write(line, 'err')

    def start(self) -> None:
        """
        Start the subprocess
        """
        from subprocess import Popen, PIPE
        from .time import Stopwatch
       
        #
        self._process = Popen(
            args = self.__args,
            cwd = self.__dir.path,
            stdout = PIPE,
            stderr = PIPE,
            text = True,
            bufsize = 1,
            errors = 'ignore'
        )

        self.wait = self._process.wait

        self._task = SysTask(self._process.pid)
        """Process Task"""

        self._stopwatch = Stopwatch()
        """Process Runtime"""
        self._stopwatch.start()

        #
        self.stdcomb = ''

        # Start Output Manager
        thread(self._stdout)

        # Start Error Manager
        thread(self._stderr)

        # Start Status Monitor
        thread(self._monitor)

        # Wait for process to complete if required
        if self._wait:
            self.wait()

    def finished(self) -> bool:
        """
        Check if the subprocess is finished
        """
        return (not self._task.exists())
    
    def running(self) -> bool:
        """
        Check if the subprocess is still running
        """
        return self._task.exists()

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
            return (self._stopwatch.elapsed() >= self.__timeout)

    def stop(self) -> None:
        """
        Stop the Subprocess
        """

        # Kill the process and its children
        self._task.stop()

        # Pause the runtime stopwatch
        self._stopwatch.stop()

    def output(self,
        format: Literal['json', 'hex'] = None,
        stream: Literal['out', 'err', 'comb'] = 'out'
    ) -> 'str | dict | list | bool | Any':
        """
        Read the output from the Subprocess
        """
        from .text import hex
        from . import json

        stream: str = getattr(self, 'std'+stream)

        output = stream.encode().strip()

        if format == 'json':
            return json.loads(output)
        
        elif format == 'hex':
            return hex.decode(output)
        
        else:
            return output

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

    def __init__(self, id:str|int):

        self.id = id
        """PID / IM"""

    def __scanner(self) -> Generator['Process']:
        """
        Scan for the main process and any of it's children
        """
        from psutil import process_iter, Process, NoSuchProcess

        main = None

        if isinstance(self.id, int):
            try:
                main = Process(self.id)
            except NoSuchProcess:
                pass

        elif isinstance(self.id, str):
            for proc in process_iter():
                if proc.name().lower() == self.id.lower():
                    main = Process(proc.pid)
                    break

        if main and main.is_running():
            try:

                for child in main.children(True):
                    if child.is_running():
                        yield child

            except NoSuchProcess:
                pass

    def cores(self, *cores:int) -> bool:
        """
        Set CPU Affinity

        Returns True upon success, and false upon failure

        Ex: Task.cores(0, 2, 4) -> Process will only use CPU cores 0, 2, & 4
        """
        from psutil import NoSuchProcess, AccessDenied

        for p in self.__scanner():
            try:
                p.cpu_affinity(cores)
                return True
            except (NoSuchProcess, AccessDenied):
                return False

    def stop(self) -> None:
        """
        Stop Process and all of it's children
        """
        for p in self.__scanner():
            p.terminate()

    def exists(self):
        """
        Check if the process is running
        """
        
        processes = list(self.__scanner())
        
        return len(processes) > 0

    def PIDs(self) -> Generator[int]:
        for p in self.__scanner():
            yield p.pid

#========================================================