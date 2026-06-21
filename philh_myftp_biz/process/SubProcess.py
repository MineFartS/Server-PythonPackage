from typing import Literal, TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..pc import Path

class SubProcess:
    """Subprocess Wrapper"""

    _hide: bool
    _wait: bool

    def __init__(self,
        args: 'list|tuple|str|Path',
        terminal: None|Literal['cmd', 'ps', 'psfile', 'py', 'pym', 'vbs'] = 'cmd',
        dir: 'Path|None' = None
    ) -> None:
        from subprocess import Popen, PIPE
        from ..array import stringify
        from .SysTask import SysTask
        from sys import executable
        from ..terminal import Log
        from ..pc import Path, cwd
        from .Thread import Thread

        # =====================================

        if dir is None:
            dir = cwd()
                    
        # =====================================

        if isinstance(args, (tuple, list)):
            args = stringify(args)
        else:
            args = [str(args)]

        if terminal is None:

            match Path(args[0]).ext:

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

        Log.VERB(f'Running Subprocess:\n{args=}\n{dir=}\nhide={self._hide}\nwait={self._wait}')

        self._process = Popen(
            args = args,
            cwd = str(dir),
            stdout = PIPE,
            stderr = PIPE,
            text = True,
            errors = 'ignore'
        )

        self._task = SysTask(self._process.pid)

        self.stop = self._task.stop

        self.send = self._process.communicate

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
        from ..terminal import _cls_cmd, cls, write
        from .Thread import Alive

        stdout = iter(self._process.stdout.read, -1)
        stderr = iter(self._process.stderr.read, -1)

        while self.running and Alive():

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

            errline = next(stderr, '')

            if len(errline) > 0:

                self.stderr += errline
                self.stdcomb += errline

                if not self._hide:
                    write(errline, 'err')

        #
        self.stop()

    @property
    def finished(self) -> bool:
        """
        Check if the subprocess is finished
        """
        return (not self.running)

    def output(self,
        format: Literal['json', 'hex'] = None,
        stream: Literal['out', 'err', 'comb'] = 'out'
    ) -> 'str | dict | list | bool | Any':
        """
        Read the output from the Subprocess
        """
        from ..text import hex
        from .. import json

        _stream: str = getattr(self, 'std'+stream)

        output = _stream.encode().strip()

        if format == 'json':
            return json.loads(output)
        
        elif format == 'hex':
            return hex.decode(output)
        
        else:
            return output.decode()

    @property
    def running(self) -> bool:
        return self._task.exists
    
    def wait(self):
        while self.running:
            pass

    def __getstate__(self):

        state = self.__dict__.copy()

        state['_process'] = None
        state['send'] = None

        return state

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