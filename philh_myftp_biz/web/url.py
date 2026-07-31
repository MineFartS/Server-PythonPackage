from typing import TYPE_CHECKING
from ..json import SupportsJSON

if TYPE_CHECKING:
    from requests import Response
    from ..pc import Path

class URL:

    @staticmethod
    def Session(max_tries:int|None):
        from requests.adapters import HTTPAdapter, Retry
        from requests import Session
        from ..num import maxint

        _retry_strat = Retry(
            total = (max_tries if max_tries else maxint),
            backoff_factor = 1,
            status_forcelist = list(range(400, 600)),
            allowed_methods = ["GET", "POST"]
        )

        _adapter = HTTPAdapter(max_retries=_retry_strat)

        _session = Session()
        _session.mount("http://", _adapter)
        _session.mount("https://", _adapter)

        return _session
    
    def __init__(self, 
        url: str
    ) -> None:
        from urllib.parse import urlparse, parse_qsl

        self.url = url.split('?')[0]

        self.headers = {}

        if '?' in url:
            self.params = dict(parse_qsl(url.split('?', 1)[1]))
        else:
            self.params = {}

        self._parsed = urlparse(url)
        self.netloc = self._parsed.netloc

        if self.netloc:
            self.addr = self.netloc
        else:
            self.addr = url    

    def copy(self):
        url = URL(self.url)
        url.params = self.params.copy()
        url.headers = self.headers.copy()
        return url

    def __str__(self):
        from urllib.parse import urlencode

        qsl = '?' + urlencode(self.params)

        url = self.url

        if len(qsl) > 1:
            url += qsl

        return url

    __repr__ = __str__
    furl: str = property(__str__)

    def child(self, name:str):
        _url = self.url.rstrip('/') + '/' + name.lstrip('/')
        url = URL(_url)
        url.params = self.params.copy()
        url.headers = self.headers.copy()
        return url

    @property
    def id(self) -> str:
        from ..text import hex

        return hex.encode([self.url, self.params])

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

    def download(self,
        path: 'Path'
    ) -> None:
        """Download file to disk"""
        from ..terminal import Log, ProgressBar

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
        from requests import head
        
        r = head(
            self.url, 
            allow_redirects = True
        )

        return int(r.headers.get('Content-Length', 0))

    def get(self,
        params: dict[str, str] = None,
        *,
        headers: dict[str, str] = None,
        stream: bool = False,
        max_tries: int | None = 1,
        timeout: None|int = 30,
        allow_redirects: bool = True
    ) -> 'Response':
        """requests.get Wrapper"""
        from requests import exceptions
        from ..terminal import Log

        if params is not None:
            self.params = params
        
        if headers is not None:
            self.headers = headers

        Log.VERB(
            'Requesting Page\n'+ \
            f'{self.furl=}\n'+ \
            f'{self.url=}\n'+ \
            f'{self.params=}\n'+ \
            f'{self.headers=}'
        )

        try:
            return self.Session(max_tries).get(
                url = self.url,
                params = self.params,
                headers = self.headers,
                stream = stream,
                timeout = timeout,
                allow_redirects = allow_redirects
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

            # Ping the address
            p = ping(
                dest_addr = self.addr,
                timeout = 3
            )

            # Return true/false if it went through
            return bool(p)
        
        except OSError:
            return False

    @property
    def hash(self) -> str:
        """Calculate the SHA256 hash of this URL"""
        from hashlib import sha256

        hasher = sha256()

        for chunk in self.stream.iter_content(chunk_size=8192):
            hasher.update(chunk)

        return hasher.hexdigest()

    def cache(self, path:'Path') -> None:
        
        if path.hash != self.hash:

            self.download(path)
