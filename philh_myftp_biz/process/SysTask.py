from psutil import process_iter, NoSuchProcess, AccessDenied
from psutil import Process as _Process
from functools import cached_property
from cpulimiter import CpuLimiter
from typing import Iterator

AccessErrors = (AccessDenied, NoSuchProcess)

def rscan(
    mutable: bool = False
):
    for proc in process_iter():
        try:
            p = Process(proc.pid)
            if (not mutable) or p.is_mutable:
                yield p
        except AccessErrors:
            pass

cpu_limiter = CpuLimiter()

class Process(_Process):

    _cpu_limit = 100

    @property
    def is_mutable(self) -> bool:
        try:
            cpu = self.cpu_affinity()
            self.cpu_affinity(cpu)
            return True
        except AccessErrors:
            return False

    @property
    def is_readable(self) -> bool:
        return (None not in [self.cwd, self.cmdline])

    @cached_property
    def cwd(self):
        from ..pc import Path
        try:
            return Path(super().cwd())
        except AccessErrors:
            pass

    @cached_property
    def cmdline(self):
        try:
            return super().cmdline()
        except AccessErrors:
            pass

    @property
    def children(self):
        try:
            return super().children()
        except AccessErrors:
            return []

    @property
    def descendants(self):
        try:
            return super().children(recursive=True)
        except AccessErrors:
            return []

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
    def _main(self) -> Process|None:
        from fnmatch import fnmatch

        if self.pid:
            try:
                return Process(self.pid)
            except AccessErrors:
                pass

        else:
            for proc in rscan():

                pname = proc.name().lower()

                if self.name and (self.name == pname):
                    return Process(proc.pid)
                elif self.pat and fnmatch(pname, self.pat):
                    return Process(proc.pid)

    def __iter__(self) -> Iterator[Process]:
        
        main = self._main

        if main:
            return iter(filter(
                lambda p: p.is_running(),    
                reversed([main, *main.descendants])
            ))
        
        else:
            return iter([])

    def stop(self) -> None:
        for p in self:
            p.terminate()

    @property
    def exists(self) -> bool:
        return len(list(self)) > 0
    
    @property
    def PIDs(self):
        yield from (p.pid for p in self)
