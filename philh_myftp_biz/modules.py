from typing import TYPE_CHECKING
from .pc import Path

if TYPE_CHECKING:
    from philh_myftp_biz.process import RunHidden
    from .process import SubProcess

class ServiceDisabledError(Exception):

    def __init__(self, serv:'Service') -> None:
        super().__init__(str(serv.path))

class Repo:

    def __init__(self, path:Path) -> None:
        from git import Repo
        
        self._repo = Repo(str(path))

        self.add  = self._repo.index.add

        self.diff = self._repo.index.diff

        self.commit = self._repo.index.commit

        self.rm   = self._repo.git.rm

        self.head = self._repo.head

        self.init = self._repo.init

        self.new_tag = self._repo.create_tag

    def refresh(self):

        self.rm('-r', '--cached', '.')

        self.add(['.'])

    def push(self):

        remote = self._repo.remotes[0]

        remote.push()

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
        from .file import YAML

        #====================================================
        # INIT

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

    def __run(self,
        func:'SubProcess',
        args: tuple[str]
    ) -> 'SubProcess':

        largs: list[str] = list(args)
        
        file: Path = self.file(args[0])

        largs[0] = str(file)

        return func(
            args = largs, 
            terminal = None
        )

    def run(self, *args:str) -> 'SubProcess':
        """Execute a new Process and wait for it to finish"""
        from .process import Run

        return self.__run(Run, args)
    
    def runH(self, *args:str) -> 'SubProcess':
        """Execute a new hidden Process and wait for it to finish"""
        from .process import RunHidden

        return self.__run(RunHidden, args)

    def start(self, *args:str) -> 'SubProcess':
        """Execute a new Process simultaneously with the current execution"""
        from .process import Start

        return self.__run(Start, args)
    
    def startH(self, *args:str) -> 'SubProcess':
        """Execute a new hidden Process simultaneously with the current execution"""
        from .process import StartHidden

        return self.__run(StartHidden, args)
    
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
        from .process import Run, RunHidden
        from shlex import split

        # Initialize a git repo if path exists
        if self.exists:
            Repo(self).init()

        runfunc = Run if show else RunHidden

        # Upgrade all python packages
        for pkg in self.packages:
            
            runfunc(
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
    EXAMPLE:
    
    ```
    serv = Service('/service/')
    ```

    './service/*'
        - Running.* (Outputs 'true' or 'false' whether the service is running)
        - Start.* (Starts the service)
        - Stop.* (Stops the service)
    """

    def __init__(self,
        path: 'str | Path',
        *args: str
    ) -> None:
        from .array import stringify

        #==============================
        # INIT

        super().__init__(path)

        self.args = stringify(args)

        self._lockfile = self.child('__pycache__/lock.ini')

        #==============================

    def file(self, name:str) -> Path:

        # Iter through all children of the service path
        for p in self.children:

            ISFILE = p.is_file
            NAMEEQ = (p.name.lower() == name.lower())
            
            if ISFILE and NAMEEQ:

                return p

        raise FileNotFoundError(f'{self.path}{name}.*')

    def _run(self, name:str) -> 'RunHidden':
        from .process import RunHidden
            
        return RunHidden(
            args = [
                self.file(name), 
                *self.args
            ],
            terminal = None,
            dir = self
        )

    def start(self,
        force: bool = False    
    ) -> None:
        """Start the Service"""
        from .terminal import Log

        Log.VERB(f"Starting Service: {self.path}")

        # Raise error if this service is disabled
        if self.enabled or force:

            self._run('Stop')
            self._run('Start')

        else:

            raise ServiceDisabledError(self)

    @property
    def running(self) -> bool:
        """Service is running"""
        from json.decoder import JSONDecodeError

        try:

            return self._run(name='Running').output(format='json') # pyright: ignore[reportReturnType]
        
        except JSONDecodeError, AttributeError, FileNotFoundError:
            return False
    
    def stop(self) -> None:
        """Stop the Service"""
        from .terminal import Log

        Log.VERB(f"Stopping Service: {self.path}")

        self._run('Stop')

    @property
    def enabled(self) -> bool:
        return ((not self._lockfile.exists) and self.exists)

    def enable(self) -> None:
        from .terminal import Log

        Log.VERB(f"Enabling Service: {self.path=}")

        # delete the lockfile
        self._lockfile.delete()

    def disable(self,
        stop: bool = True
    ) -> None:
        from .terminal import Log

        Log.VERB(f"Disabling Service: {self.path=}")

        #
        self._lockfile.parent.mkdir()

        # Create the lock file
        self._lockfile.open('w')
        
        if stop:
            self.stop()
