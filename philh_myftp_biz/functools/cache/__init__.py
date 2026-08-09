from functools import cached_property as _cached_property
from typing import Any

from .transitory import TransitoryCache # pyright: ignore[reportUnusedImport]
from .prop import cached_property # pyright: ignore[reportUnusedImport]

def clear_cache(instance: Any) -> None:

    for name, value in vars(instance).items():

        if isinstance(value, _cached_property):

            delattr(instance, name)

# ======================================

class _diskcache:

    def __call__(self, 
        expire: int|None = None
    ):
        from diskcache import Cache
        from ...pc import loc

        if not hasattr(self, 'cache'):
            self.cache = Cache(loc.cache.path)

        return self.cache.memoize(expire=expire)

diskcache = _diskcache()

# ======================================

