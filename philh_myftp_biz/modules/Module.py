from typing import TYPE_CHECKING
from ..pc import Path

if TYPE_CHECKING:
    from ..process import SubProcess

class Module(Path):
    """
    Allows for easy interaction with other languages in a directory

    Make sure to add a file labed 'Module.yaml' in the directory
    'Module.yaml' needs to be configured with the following syntax:
    \"""
        packages: []
    \"""

    EXAMPLE:
    ```
    m = Module('E:/testmodule')

    # Runs any script with a path starting with "E:/testmodule/main.###"
    # Handlers for the extensions are automatically interpreted
    m.run('main')

    # 'E:/testmodule/sub/script.###'
    m.run('sub/script')
    
    ```
    """

    def __init__(self,
        module: 'str | Path'
    ) -> None:
        from ..process import SubVenv
        from ..file import YAML

        super().__init__(module)

        #====================================================
        # LOAD CONFIGURATION

        configFile = self.child('/module.yaml')

        if configFile.exists:

            config: dict = YAML(configFile).read()

            self.packages: list[str] = config['packages']

        else:
            self.packages = []

        #====================================================

        _py = self.child('/.venv/')

        if _py.exists:
            self.venv = SubVenv(_py)
        else:
            self.venv = None

    def _run(self,
        func: 'SubProcess',
        args: tuple[str]
    ) -> 'SubProcess':

        file: Path = self.file(args[0])

        largs: list[str] = list(args)
        largs[0] = str(file)

        self.venv and self.venv.enable()

        try:
            return func(
                *largs, 
                terminal = None,
                dir = self
            )
        finally:
            self.venv and self.venv.disable()

    def run(self, *args:str) -> 'SubProcess':
        """Execute a new Process and wait for it to finish"""
        from ..process import Run

        return self._run(Run, args)
    
    def runH(self, *args:str) -> 'SubProcess':
        """Execute a new hidden Process and wait for it to finish"""
        from ..process import RunHidden

        return self._run(RunHidden, args)

    def start(self, *args:str) -> 'SubProcess':
        """Execute a new Process simultaneously with the current execution"""
        from ..process import Start

        return self._run(Start, args)
    
    def startH(self, *args:str) -> 'SubProcess':
        """Execute a new hidden Process simultaneously with the current execution"""
        from ..process import StartHidden

        return self._run(StartHidden, args)
    
    def cap(self, *args:str):
        """Execute a new hidden Process and capture the output as JSON"""
        return self.runH(*args).output(format='json')

    def file(self,
        *name: str
    ) -> 'Path':
        """
        Find a file by it's name

        Returns FileNotFoundError if file does not exist

        EXAMPLE:

        # "run.py"
        m.file('run')

        # "web/script.js"
        m.file('web', 'script')
        m/file('web/script')
        """

        parts: list[str] = []
        for n in name:
            parts += n.split('/')
        
        dir = self.child('/'.join(parts[:-1]))

        for p in dir.children:
            
            if p.is_file and ((p.name.lower()) == (parts[-1].lower())):
                
                return p

        raise FileNotFoundError(dir.path + parts[-1] + '.*')

    def install(self,
        show: bool = True
    ) -> None:
        """Automatically install all dependencies"""
        from shlex import split

        if show:
            from ..process import Run
        else:
            from ..process import RunHidden as Run

        self.venv and self.venv.enable()

        # Upgrade all python packages
        for pkg in self.packages:
            
            Run(
                'pip', 'install',
                *split(pkg),
                '--user',
                '--no-warn-script-location', 
                '--upgrade',
                terminal = 'pym'
            )

        self.venv and self.venv.disable()
