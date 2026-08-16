from requests.adapters import HTTPAdapter as _HTTPAdapter
from requests_cache import CachedSession as _CachedSession
from urllib3.util import Retry as _Retry

class RetryStrat(_Retry):

    def __init__(self,
        total: int = 0,
        backoff_factor: int = 1,
        status_forcelist = range(400, 600),
        allowed_methods = ["GET", "POST"],
        **kwargs
    ): super().__init__(
        total = total,
        backoff_factor = backoff_factor, 
        status_forcelist = status_forcelist, 
        allowed_methods = allowed_methods, 
        **kwargs
    )

class Adapter(_HTTPAdapter):

    def __init__(self,
        retry_strategy: RetryStrat = None
    ): super().__init__(
        max_retries = retry_strategy
    )

class Session(_CachedSession):

    def __init__(self,
        name: str,
        max_age: int = -1,
        adapter: Adapter = None
    ):
        from ..pc import loc

        super().__init__(
            cache_name = loc.cache.child(f'{name}.sqlite').path,
            backend = 'sqlite',
            expire_after = max_age
        )

        if adapter:
            self.mount("http://", adapter)
            self.mount("https://", adapter)

