from typing import Generator, TYPE_CHECKING

if TYPE_CHECKING:
    from .pc import Path
    from .__init__ import run

def output(data) -> None:
    """
    Print the data to the terminal as hexidecimal, then exit
    """
    from .text import hex
    from .pc import cls

    cls()
    print(';' + hex.encode(data) + ';')
    exit()

def input() -> list:
    """
    Decode Command Line Arguements
    """
    from .__init__ import Args
    from .text import hex

    return hex.decode(Args()[0])

def when_modified(*modules:'Module') -> Generator['WatchFile']:
    """
    Wait for any Watch File to be modified

    EXAMPLE:
    m1 = Module('C:/module1/')
    m2 = Module('C:/module2/')

    gen = modules.when_modified(m1, m2)

    for watchfile in gen:
        {Code to run when a watchfile is modified}
    """
    from .time import sleep

    watch_files: list['WatchFile'] = []

    for module in modules:
        watch_files += module.watch_files

    while True:
        for wf in watch_files:
            if wf.modified():
                yield wf

        sleep(.25)

def Scanner() -> Generator['Module']:
    """
    Scan for modules in the 'E:/' directory
    """
    from .pc import Path
    
    path = Path('E:/')
    
    for p in path.children():
    
        try:
            yield Module(p)
        
        except ModuleNotFoundError:
            pass

class ModuleDisabledError(Exception):
    def __init__(self, module:'Module'):
        super().__init__(module.dir.path)

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
    
    m = Module('E:/testmodule')

    # Runs any script with a path starting with "E:/testmodule/main.###"
    # Handlers for the extensions are automatically interpreted
    m.run('main')

    # 'E:/testmodule/sub/script.###'
    m.run('sub', 'script')
    m.run('sub/script')
    """

    def __init__(self,
        module: 'str | Path'
    ):
        from .pc import Path
        from .file import YAML

        self.dir = Path(module)

        if self.dir.isfile():
            raise ModuleNotFoundError(self.dir.path)

        configFile = self.dir.child('/module.yaml')

        if not configFile.exists():
            raise ModuleNotFoundError(self.dir.path)

        self.name = self.dir.name()

        config = YAML(configFile).read()

        self.enabled = config['enabled']

        self.packages: list[str] = config['packages']

        self.watch_files: list[WatchFile] = []
        for WFpath in config['watch_files']:
            self.watch_files += [WatchFile(
                module = self,
                path = WFpath
            )]

    def run(self,
        *args,
        hide: bool = False
    ) -> 'None | Process':
        """
        Execute a new Process and wait for it to finish
        """
        if self.enabled:
            return Process(
                module = self,
                args = list(args),
                hide = hide,
                wait = True
            )
        else:
            raise ModuleDisabledError(self)

    def start(self,
        *args,
        hide: bool = False
    ) -> 'None | Process':
        """
        Execute a new Process simultaneously with the current execution
        """
        if self.enabled:
            return Process(
                module = self,
                args = list(args),
                hide = hide,
                wait = False
            )
        else:
            raise ModuleDisabledError(self)
        
    def cap(self,
        *args
    ):
        """
        Execute a new Process and capture the output as JSON
        """

        p = self.run(
            *args,
            hide = True
        )

        return p.output('json')

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

    def install(self,
        hide: bool = False
    ) -> None:
        """
        Automatically install all dependencies
        """
        from .__init__ import run

        # Initialize a git repo
        self.git('init', hide=hide)

        # Upgrade all python packages
        for pkg in self.packages:
            run(
                args = ['pip', 'install', '--upgrade', pkg],
                wait = True,
                terminal = 'pym',
                hide = hide
            )

    def watch(self) -> Generator['WatchFile']:
        """
        Returns a modules.when_modified generator for the current module
        """
        return when_modified(self)

    def __str__(self):
        return self.dir.path

    def git(self,
        *args,
        hide: bool = False
    ) -> 'run':
        from .__init__ import run

        return run(
            args = ['git', *args],
            wait = True,
            dir = self.dir,
            hide = hide
        )

class Process:
    """
    Wrapper for Subprocesses started by a Module
    """

    def __init__(self,
        module: Module,
        args: list[str],
        hide: bool,
        wait: bool
    ):
        from .text import hex
        from .__init__ import run

        file = module.file(args[0])
        args[0] = file.path

        self.__isPY = (file.ext() == 'py')
        if self.__isPY:
            args = [args[0], hex.encode(args[1:])]

        self.__p = run(
            args = args,
            wait = wait,
            hide = hide,
            terminal = 'ext',
            cores = 3
        )

        self.start    = self.__p.start
        self.stop     = self.__p.stop
        self.restart  = self.__p.restart
        self.finished = self.__p.finished
        self.output   = self.__p.output

class WatchFile:
    """
    Watch File for Module
    """

    def __init__(self,
        module: 'Module',
        path: str
    ):
        from .pc import Path
        
        if path.startswith('/'):
            self.path = module.dir.child(path)
        else:
            self.path = Path(path)

        self.module = module

        self.__mtime = self.path.var('__mtime__')
        
        self.__mtime.save(
            value = self.path.mtime.get().unix
        )

    def modified(self) -> bool:
        """Check if the file has been modified"""
        
        return (self.__mtime.read() != self.path.mtime.get().unix)

class Service:
    """
    """

    def __init__(self,
        module: Module,
        path: str,
        *args
    ):
        
        self.__mod = module
        
        if path.endswith('/'):
            self.__path = path
        else:
            self.__path = path+'/'

        self.__args = args

    def Start(self,
        force: bool = True
    ):
        """
        Start the Service
        
        Will do nothing if already running unless force is True
        """
        if force or (not self.Running()):
            self.__mod.run(
                self.__path+'Start', *self.__args,
                hide = True
            )

    def Running(self) -> bool:
        """
        Service is running
        """
        return self.__mod.cap(self.__path+'Running')
    
    def Stop(self) -> None:
        """
        Stop the Service
        """
        self.__mod.run(
            self.__path+'Stop', *self.__args,
            hide = True
        )