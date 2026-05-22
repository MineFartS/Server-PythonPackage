from typing import TYPE_CHECKING, TypedDict
from .supports import SupportsStr
from ..json.Dict import Dict

if TYPE_CHECKING:
    from ..time import Timeout

class CachedItem[T](TypedDict):
    time: Timeout
    value: T

class TransitoryCache[T](Dict[CachedItem[T]]):

    def __init__(self, 
        id: SupportsStr = 0, 
        expire: int = 18_000
    ) -> None:
        from ..pc import loc

        self.expire = expire

        file = loc.cache.child(f'TransitoryCache-{id}.pkl')
        super().__init__(file.PKL)

    def __getitem__(self, key:str) -> T | None:

        item = super().__getitem__(key)

        if item is None:
            pass

        elif item['time'].timed_out:
            super().__delitem__(key)

        else:
            return item['value'] # pyright: ignore[reportReturnType]
            
    def __setitem__(self, key:str, value:T) -> None:
        from ..time import Timeout

        super().__setattr__(key, {
            'time': Timeout(self.expire),
            'value': value
        })

