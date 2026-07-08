from .supports import SupportsStr, SupportsJSON
from typing import TYPE_CHECKING, TypedDict
from ..json.Dict import Dict

if TYPE_CHECKING:
    from ..time import Timeout

class CachedItem[T](TypedDict):
    time: 'Timeout'
    value: T

class TransitoryCache[T](Dict[CachedItem[T]]):

    def __init__(self, 
        id: SupportsStr = 0, 
        expire: int = 18_000
    ) -> None:
        from ..pc import loc

        self.expire = expire

        file = loc.temp.child(f'TransitoryCache-{id}.pkl')
        self.clear = file.delete

        super().__init__(file.PKL)

    def _repair(self) -> None:
        from _pickle import UnpicklingError
        
        try:
            self.read()
        except (EOFError, UnpicklingError):
            self.save({})

    def __getitem__(self, key:SupportsJSON) -> T | None:
        from ..json import dumps

        _key = dumps(key)

        self._repair()

        item = super().__getitem__(_key)
         
        if item is None:
            pass

        elif item['time'].timed_out:
            super().__delitem__(_key)

        else:
            return item['value'] # pyright: ignore[reportReturnType]
            
    def __setitem__(self, key:SupportsJSON, value:T) -> None:
        from ..time import Timeout
        from ..json import dumps

        self._repair()

        super().__setitem__(
            key = dumps(key), 
            value = {
                'time': Timeout(self.expire),
                'value': value
            }
        )

    def __contains__(self, key:SupportsJSON) -> bool:
        from ..json import dumps

        self._repair()

        return super().__contains__(dumps(key))

