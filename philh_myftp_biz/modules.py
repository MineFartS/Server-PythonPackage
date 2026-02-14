from typing import TYPE_CHECKING
from git import Repo as __Repo
from .pc import Path

class ServiceDisabledError(Exception):

    def __init__(self, serv:'Service'):
        super().__init__(str(serv.path))

if TYPE_CHECKING:
    from .process import SubProcess
    from .pc import Path

class Repo(__Repo):

    def __init__(self, path:Path):
        
        super().__init__(str(path))

        try:
            self.REMOTE = self.remotes[0]
        except:
            self.REMOTE = None

    def refresh(self):

        self.git.rm('-r', '--cached', '.')

        self.index.add(['.'])

class Module(Path, Repo):
    """
    Allows for easy interaction with other languages in a directory

    Make sure to add a file labed 'Module.yaml' in the directory
    'Module.yaml' needs to be configured with the following syntax:
    \"""
        enabled: False
        packages: []
        watch_files: []
    \"""

    EXAMPLE:
    ```
    m = Module('E:/testmodule')

    # Runs any script with a path starting with "E:/testmodule/main.###"
    # Handlers for the extensions are automatically interpreted
    m.run('main')

    # 'E:/testmodule/sub/script.###'
    m.run('sub', 'script')
    m.run('sub/script')
    
    ```
    """

    def __init__(self,
        module: 'str | Path'
    ):
        from .file import YAML

        #====================================================
        # INIT

        Path.__init__(self, module)
        Repo.__init__(self, self)

        #====================================================
        # LOAD CONFIGURATION

        configFile = self.child('/module.yaml')

        if configFile.exists():

            config = YAML(configFile).read()

            self.packages: list[str] = config['packages']

        else:
            self.packages = []

        #====================================================

    def run(self, *args) -> 'SubProcess':
        """
        Execute a new Process and wait for it to finish
        """
        from .process import Run

        args = list(args)
        args[0] = str(self.file(args[0]))

        return Run(args, terminal='ext')
    
    def runH(self, *args) -> 'SubProcess':
        """
        Execute a new hidden Process and wait for it to finish
        """
        from .process import RunHidden

        args = list(args)
        args[0] = str(self.file(args[0]))

        return RunHidden(args, terminal='ext')

    def start(self, *args) -> 'SubProcess':
        """
        Execute a new Process simultaneously with the current execution
        """
        from .process import Start

        args = list(args)
        args[0] = str(self.file(args[0]))

        return Start(args, terminal='ext')
    
    def startH(self, *args) -> 'SubProcess':
        """
        Execute a new hidden Process simultaneously with the current execution
        """
        from .process import Run

        args = list(args)
        args[0] = str(self.file(args[0]))

        return Run(args, terminal='ext')
    
    def cap(self, *args):
        """
        Execute a new hidden Process and capture the output as JSON
        """
        return self.runH(*args).output('json')

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

        for p in dir.children():
            
            if p.isfile() and ((p.name().lower()) == (parts[-1].lower())):
                
                return p

        raise FileNotFoundError(dir.path + parts[-1] + '.*')

    def install(self) -> None:
        """
        Automatically install all dependencies
        """
        from .process import Run
        from shlex import split

        # Initialize a git repo
        self.init()

        # Upgrade all python packages
        for pkg in self.packages:
            
            Run(
                args = [
                    'pip', 'install',
                    *split(pkg),
                    '--user',
                    '--no-warn-script-location', 
                    '--upgrade'
                ],
                terminal = 'pym'
            )

class Service(Path):
    """
    Wrapper for Module Service

    EXAMPLE:
    
    mod = Module('E:/module/')
    path = '/service/'

    serv = Service(mod, path)

    'E:/module/service/*'
        - Running.* (Outputs 'true' or 'false' whether the service is running)
        - Start.* (Starts the service)
        - Stop.* (Stops the service)
    """

    def __init__(self,
        path: 'str | Path',
        args: list[str] = []
    ):
        from .array import stringify

        #==============================
        # INIT

        Path.__init__(self, path)

        self.args = stringify(args)
        
        #==============================

        self.__lockfile = self.child('__pycache__/lock.ini')

        self.Enable = self.__lockfile.delete

        #==============================

    def _run(self, name:str):
        from .process import RunHidden

        # Iter through all children of the service path
        for p in self.children():

            ISFILE = p.isfile()
            NAMEEQ = (p.name().lower() == name.lower())
            
            if ISFILE and NAMEEQ:

                # Grant full access to file
                p.set_access.full()

                # Run the file
                return RunHidden(
                    args = [p, *self.args],
                    terminal = 'ext'
                )

        raise FileNotFoundError(f'{self.path}{name}.*')

    def Start(self):
        """
        Start the Service
        """
        from .terminal import Log

        Log.VERB(f"Starting Service: {self.path=}")

        # Raise error if this serivce is disabled
        if self.Enabled():

            self.Stop()
            self._run('Start')

        else:

            raise ServiceDisabledError(self)

    def Running(self) -> bool:
        """
        Service is running
        """
        from json.decoder import JSONDecodeError

        try:
            return self._run('Running').output('json')
        
        except JSONDecodeError, AttributeError, FileNotFoundError:
            return False
    
    def Stop(self) -> None:
        """
        Stop the Service
        """
        from .terminal import Log

        Log.VERB(f"Stopping Service: {self.path=}")

        self._run('Stop')

    def Enabled(self) -> bool:
        """
        """
        from .terminal import Log

        Log.VERB(f"Enabling Service: {self.path=}")
        
        return (not self.__lockfile.exists())

    def Disable(self,
        stop: bool = True
    ) -> None:
        """"""
        from .terminal import Log
        from .pc import mkdir

        Log.VERB(f"Disabling Service: {self.path=}")

        #
        mkdir(self.__lockfile.parent())

        # Create the lock file
        self.__lockfile.open('w')
        
        if stop:
            self.Stop()
