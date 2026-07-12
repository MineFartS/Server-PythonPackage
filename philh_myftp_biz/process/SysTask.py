from psutil import process_iter, NoSuchProcess, AccessDenied
from psutil import Process as _Process
from cpulimiter import CpuLimiter
from typing import Iterator

def rscan(writeable:bool=False):
    for proc in process_iter():
        try:
            cpu = proc.cpu_affinity()
            if writeable: proc.cpu_affinity(cpu)
            yield Process(proc.pid)
        except (AccessDenied, NoSuchProcess):
            pass

cpu_limiter = CpuLimiter()

class Process(_Process):

    _cpu_limit = 100

    @property
    def is_writeable(self) -> bool:
        try:
            cpu = self.cpu_affinity()
            self.cpu_affinity(cpu)
            return True
        except (AccessDenied, NoSuchProcess):
            return False

    def cpu_limit(self, percent:int=None):
        
        if percent is None:
            return # TODO return current percent
        
        if not (1 <= percent <= 100):
            raise ValueError("Percentage must be between 1 and 100")

        if self._cpu_limit != percent:
            
            self._cpu_limit = percent

            cpu_limiter.add(
                pid = self.pid,
                limit_percentage = percent
            )

class SysTask:
    """
    System Task

    Wrapper for psutil.Process
    """

    pid = None
    """Process ID"""

    name = None
    """Process Name"""
    
    pat = None
    """Process Name [Wildcard]"""

    def __init__(self,
        id: str | int
    ) -> None:
        
        self.id = id

        if isinstance(id, int):
            self.pid = id

        elif '*' in id:
            self.pat = id.lower()
        
        else:                
            self.name = id.lower()

    @property
    def _main(self) -> _Process|None:
        from ..text import like

        if self.pid:

            try:
                return Process(self.pid)
            except NoSuchProcess:
                pass

        else:

            for proc in process_iter():

                pname = proc.name().lower()

                if self.name and (self.name == pname):
                    return Process(proc.pid)
                
                elif self.pat and like(pname, self.pat):
                    return Process(proc.pid)

    def __iter__(self) -> Iterator[_Process]:
        
        main = self._main

        # IF main process found
        if main:

            processes = [main]

            try:
                processes += main.children(recursive=True)

            except NoSuchProcess:
                pass

            return iter(filter(
                lambda p: p.is_running(),    
                reversed(processes)
            )) # pyright: ignore[reportReturnType]
        
        else:

            return iter([])

    def stop(self) -> None:
        """Stop Process and all of it's children"""
        from ..terminal import Log

        Log.VERB(f'Stopping Process: {self.id}')

        for p in self:
            
            p.terminate()

    @property
    def exists(self) -> bool:
        """Check if the process is running"""

        return len(list(self)) > 0
    
    @property
    def PIDs(self):
        
        for process in self:

            yield process.pid

