from typing import Callable, TYPE_CHECKING, cast

if TYPE_CHECKING:
    from .time import Timeout

#========================================================
# DISK CACHE

class TransitoryCache[T](dict[str, 'dict[str, T|Timeout]']):

    def __init__(self, 
        id: str|int = 0, 
        expire: int = 18_000
    ) -> None:
        from .file import PKL
        from .pc import loc

        self.expire = expire

        file = loc.cache.child(f'TransitoryCache-{id}.pkl')

        self.pkl = PKL(file).Dict

        super().__init__(self.pkl.read())
    
    def __del__(self) -> None:

        data = cast(dict, self)
        
        self.pkl.save(data)

    def __getitem__(self, key) -> T | None:
        from .text import hex

        key = hex.encode(key)

        if key in self:

            item = super().__getitem__(key)

            if item['time'].timed_out:
                self.__delitem__(key)
            else:
                return item['value'] # pyright: ignore[reportReturnType]

    def __setitem__(self, key, value:T) -> None:
        from .time import Timeout
        from .text import hex

        key = hex.encode(key)

        super().__setitem__(key, {
            'time': Timeout(self.expire),
            'value': value
        })

    def __contains__(self, key):
        from .text import hex

        key = hex.encode(key)

        return super().__contains__(key)

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