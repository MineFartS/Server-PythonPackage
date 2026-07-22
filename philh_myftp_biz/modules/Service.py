from functools import cached_property
from typing import TYPE_CHECKING
from ..pc import Path

if TYPE_CHECKING:
    from philh_myftp_biz.process import RunHidden

class ServiceDisabledError(Exception):

    def __init__(self, serv:'Service') -> None:
        super().__init__(str(serv.path))

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
        from ..array import stringify

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
        from ..process import RunHidden
            
        return RunHidden(
            self.file(name), 
            *self.args,
            terminal = None,
            dir = self
        )

    def start(self,
        force: bool = False    
    ) -> None:
        """Start the Service"""
        from ..terminal import Log

        Log.VERB(f"Starting Service: {self.path}")

        if force:
            pass
        elif self.running:
            return
        elif not self.enabled:
            raise ServiceDisabledError(self)

        self._run('Stop')
        self._run('Start')

    @property
    def running(self) -> bool:
        """Service is running"""
        from json.decoder import JSONDecodeError

        try:
            return self._run(name='Running').output(format='json') # pyright: ignore[reportReturnType]
        
        except (JSONDecodeError, AttributeError, FileNotFoundError, PermissionError):
            return False
    
    def stop(self) -> None:
        """Stop the Service"""
        from ..terminal import Log

        Log.VERB(f"Stopping Service: {self.path}")

        self._run('Stop')

    @property
    def enabled(self) -> bool:
        return ((not self._lockfile.exists) and self.exists)

    def enable(self) -> None:
        from ..terminal import Log

        Log.VERB(f"Enabling Service: {self.path=}")

        # delete the lockfile
        self._lockfile.delete()

    def disable(self,
        stop: bool = True
    ) -> None:
        from ..terminal import Log

        Log.VERB(f"Disabling Service: {self.path=}")

        #
        self._lockfile.parent.mkdir()

        # Create the lock file
        self._lockfile.open('w')
        
        if stop:
            try: self.stop()
            except: pass

    @cached_property
    def logfile(self):
        
        files = list(self.child('__pylogs__').children)
        
        if len(files) > 0:
            return max(files, 
                key = lambda f: int(f.mtime)
            )

