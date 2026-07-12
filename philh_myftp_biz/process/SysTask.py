from psutil import process_iter, Process, NoSuchProcess, AccessDenied
from typing import Iterator

def rscan(writeable:bool=False):
    for proc in process_iter():
        try:
            cpu = proc.cpu_affinity()
            if writeable: proc.cpu_affinity(cpu)
            yield proc
        except (AccessDenied, NoSuchProcess):
            pass

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
    def _main(self) -> Process|None:
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

                    return proc
                
                elif self.pat and like(pname, self.pat):

                    return proc

    def __iter__(self) -> Iterator[Process]:
        
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

