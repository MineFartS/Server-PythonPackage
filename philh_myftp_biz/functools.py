from functools import cached_property
from dataclasses import dataclass
from typing import Any, Callable
from .pc import loc

#========================================================
# DISK CACHE

@dataclass
class TransitoryCache[T]:

    id: str|int = 0
    expire: int = 18000

    @cached_property
    def _file(self):
        from .pc import loc

        return loc.cache.child(f'philh_myftp_biz-{self.id}.pkl')

    @cached_property
    def _dict(self):
        from .json import Dict
        from .file import PKL

        pkl = PKL(
            path = self._file,
            default = {}
        )

        return Dict(pkl)

    def __getitem__(self, key:Any) -> T | None:
        from .time import Timeout

        if self._dict[key]:

            time: Timeout = self._dict[key]['time']

            try:

                time.check()
                
                return self._dict[key]['value']
            
            except TimeoutError:
                del self._dict[key]

    def __setitem__(self, key:Any, value:T) -> None:
        from .time import Timeout

        self._dict[key] = {}

        self._dict[key]['time'] = Timeout(self.expire) 

        self._dict[key]['value'] = value

#========================================================

def single_use(f): # pyright: ignore[reportMissingParameterType]
    """Ignore all but first executions"""
    from functools import wraps

    @wraps(f)
    def wrapper(*args, **kwargs): # pyright: ignore[reportMissingParameterType]
        
        if not wrapper.has_run:
            
            wrapper.has_run = True
            
            return f(*args, **kwargs)
    
    wrapper.has_run = False

    return wrapper

def waitfor(
    func: Callable[..., bool]
) -> None:

    while not func():
        pass

#========================================================