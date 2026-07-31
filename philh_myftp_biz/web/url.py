from typing import TYPE_CHECKING
from ..json import SupportsJSON
from ..pc import loc

if TYPE_CHECKING:
    from requests import Response
    from ..pc import Path

_dbfile = loc.cache.child('URL.sqlite')

class URL:
    
    def __init__(self, 
        url: str,
        *,
        params: dict[str, str] = {},
        headers: dict[str, str] = {},
        max_tries: int | None = 1,
        max_age: int = 0,
        timeout: None|int = 30
    ) -> None:
        from urllib.parse import urlparse, parse_qsl
        from requests.adapters import HTTPAdapter
        from requests_cache import CachedSession
        from urllib3.util import Retry
        from ..num import maxint

        self.url = url.split('?')[0]
        self.params  = params.copy()
        self.headers = headers.copy()
        self.timeout = timeout
        self.addr = urlparse(url).netloc or url

        if '?' in url:
            self.params |= parse_qsl(url.split('?', 1)[1])

        _retry_strat = Retry(
            total = (max_tries or maxint),
            backoff_factor = 1,
            status_forcelist = range(400, 600),
            allowed_methods = ["GET", "POST"]
        )

        _adapter = HTTPAdapter(max_retries=_retry_strat)

        self._session = CachedSession(
            cache_name = _dbfile.path,
            backend = 'sqlite',
            expire_after = max_age
        )
        self._session.mount("http://", _adapter)
        self._session.mount("https://", _adapter)

        self.kwargs = {
            'url': self.url,
            'params': self.params.copy(),
            'headers': self.headers.copy(),
            'max_tries': max_tries,
            'timeout': timeout
        }.copy()

    def __str__(self):
        from urllib.parse import urlencode

        if len(self.params) == 0:
            return self.url
        else:
            return self.url + '?' + urlencode(self.params)

    __repr__ = __str__
    furl: str = property(__str__)

    def copy(self, **kwargs):
        return URL(**(self.kwargs | kwargs))

    def child(self, name:str, **kwargs):
        return self.copy(
            url = (self.url.rstrip('/') + '/' + name.lstrip('/')),
            **kwargs
        )

    @property
    def stream(self):
        return self.get(stream=True)

    @property
    def content(self):
        return self.get().content
    
    @property
    def text(self) -> str:
        return self.get().text

    @property
    def json(self) -> SupportsJSON:
        return self.get().json()
    
    @property
    def head(self) -> 'Response':
        return self._session.head()

    @property
    def exists(self):
        return self.head.status_code < 400

    def download(self,
        path: 'Path',
        force: bool = True
    ) -> None:
        """Download file to disk"""
        from ..terminal import Log, ProgressBar

        if (not force) and (path.hash == self.hash):
            return

        Log.VERB(f'Downloading File:\nurl={self.url}\n{path=}')

        file = path.open(mode='wb')

        pbar = ProgressBar(
            total = self.size,
            label = "Downloading File",
            mode = 'FSTREAM',
            verbose = True
        )

        for data in self.stream.iter_content(1024):

            pbar.step(data)

            file.write(data)

        file.close()

    @property
    def size(self) -> int:
        return int(self.head.headers.get('Content-Length', 0))

    def get(self, **kwargs) -> 'Response':
        """requests.get Wrapper"""
        from requests import exceptions
        from ..terminal import Log

        Log.VERB(
            'Requesting Page\n'+ \
            f'{self.furl=}\n'+ \
            f'{self.url=}\n'+ \
            f'{self.params=}\n'+ \
            f'{self.headers=}'
        )

        try:
            return self._session.get(
                url = self.url,
                params = self.params,
                headers = self.headers,
                timeout = self.timeout,
                allow_redirects = True,
                **kwargs
            )
        except exceptions.RetryError as e:
            raise TimeoutError() from e
        
        except exceptions.ConnectionError as e:
            raise ConnectionError() from e

    @property
    def online(self) -> bool:
        """ping3.ping wrapper"""
        from ping3 import ping

        try:
            return bool(ping(
                dest_addr = self.addr,
                timeout = 3
            ))
        
        except OSError:
            return False

    @property
    def hash(self) -> str:
        """Calculate the SHA256 hash"""
        from hashlib import sha256

        hasher = sha256()

        for chunk in self.stream.iter_content(chunk_size=8192):
            hasher.update(chunk)

        return hasher.hexdigest()
