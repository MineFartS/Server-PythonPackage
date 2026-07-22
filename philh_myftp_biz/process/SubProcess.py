from typing import Literal, TYPE_CHECKING, Any
from .Thread import ThreadedFunc
from sys import executable

if TYPE_CHECKING:
    from ..pc import Path
    from ..text import UnconsumingIO

TerminalMap = {

    'cmd': ['cmd', '/c'],

    'ps': ['Powershell', '-Command'],

    'psfile': ['Powershell', '-File'],

    'py': [executable],

    'pym': [executable, '-m'],
        
    'vbs': ['wscript']
}

class SubProcess:
    """Subprocess Wrapper"""

    _hide: bool
    _wait: bool

    def __init__(self,
        *args: 'str|Path',
        terminal: None|Literal['cmd', 'ps', 'psfile', 'py', 'pym', 'vbs'] = 'cmd',
        dir: 'Path|None' = None
    ) -> None:
        from subprocess import Popen, PIPE
        from ..text import UnconsumingIO
        from ..array import stringify
        from .SysTask import SysTask
        from ..terminal import Log
        from ..pc import Path, cwd

        # =====================================

        if len(args) == 1 and isinstance(args[0], (list, tuple)):
            args = args[0] # TODO: Temporary Backwards Compatibility

        # =====================================

        if dir is None:
            dir = cwd()
                    
        # =====================================

        if terminal is None:
            match Path(args[0]).ext:

                case 'ps1': terminal='psfile'

                case 'py': terminal='py'

                case 'exe': terminal='cmd'

                case 'bat': terminal='cmd'

                case 'vbs': terminal='vbs'

                case _: terminal='cmd'
                
        if not isinstance(args, (tuple, list)):
            args = [args]

        args = TerminalMap.get(terminal) + stringify(args)

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

        self.stdout = UnconsumingIO(self._process.stdout, False)
        self.stderr = UnconsumingIO(self._process.stderr, False)

        # =====================================

        if not self._hide:
            self.__print()

        # Wait for process to complete if required
        if self._wait:
            self.wait()

    @property
    def finished(self) -> bool:
        """
        Check if the subprocess is finished
        """
        return (not self.running)

    def output(self,
        format: Literal['json', 'hex'] = None,
        stream: Literal['out', 'err'] = 'out'
    ) -> 'str | dict | list | bool | Any':
        """Read the output from the Subprocess"""
        from ..text import hex
        from .. import json

        _stream: UnconsumingIO = getattr(self, 'std'+stream)

        output = _stream.read()

        if format == 'json':
            return json.loads(output)
        
        elif format == 'hex':
            return hex.decode(output)
        
        else:
            return output

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

    @ThreadedFunc
    def __print(self) -> None:
        from ..terminal import write

        while self.running:
            write(self.stdout._read(), 'out', True)
            write(self.stderr._read(), 'err', True)

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