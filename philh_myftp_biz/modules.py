from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .process import SubProcess
    from .pc import Path

class Module:
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
        from .pc import Path

        #====================================================

        self.dir = Path(module)

        self.name = self.dir.name()

        #====================================================
        # CONFIG

        configFile = self.dir.child('/module.yaml')

        if not configFile.exists():
            raise ModuleNotFoundError(self.dir.path)

        config = YAML(configFile).read()

        self.packages: list[str] = config['packages']

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
        
        dir = self.dir.child('/'.join(parts[:-1]))

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
        self.git('init')

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

    def git(self, *args) -> 'SubProcess':
        from .process import Run

        return Run(
            args = ['git', *args],
            dir = self.dir
        )

class Service:
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
        module: Module,
        path: str
    ):
        
        self.module = module

        # ================================

        if not path.startswith('/'):
            path = '/'+path

        if not path.endswith('/'):
            path += '/'

        self.__path = path

        self.path = (module.name + path)

        # ================================

        self.name = self.path.split('/')[-2]

        # ================================

    def Start(self,
        force: bool = False
    ):
        """
        Start the Service
        
        Will do nothing if already running unless force is True
        """

        arg = self.__path+'Start'

        if force:

            self.Stop()

            self.module.runH(arg)

        elif not self.Running():
            
            self.module.runH(arg)

    def Running(self) -> bool:
        """
        Service is running
        """
        from json.decoder import JSONDecodeError

        try:
            return self.module.cap(self.__path+'Running')
        
        except JSONDecodeError, AttributeError:
            return False
    
    def Stop(self) -> None:
        """
        Stop the Service
        """
        self.module.runH(self.__path+'Stop')
