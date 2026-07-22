from typing import Literal, TYPE_CHECKING
from functools import cached_property
from ..classtools import singleton
from ..json import SupportsJSON

if TYPE_CHECKING:
    from requests import Response
    from ..pc import Path

@singleton
class IP:

    @cached_property
    def LAN(self) -> str:
        from socket import gethostname, gethostbyname

        return gethostbyname(gethostname())
    
    @cached_property
    def WAN(self) -> str:
        return URL('https://api.ipify.org').text
    
    @cached_property
    def ROUTER(self) -> str:
        from netifaces import gateways, AF_INET

        return gateways().get('default', {}).get(AF_INET)[0]

class Port:
    """Details of a port on a network device"""

    def __init__(self,
        port: int,
        host: str = '127.0.0.1'
    ) -> None:
        
        self.port: int = port

        self.addr: tuple[str, int] = (host, port)

    @property
    def listening(self) -> bool:
        """Check if Port is listening/in use"""

        from socket import error, SHUT_RDWR
        from quicksocketpy import socket

        sock = socket()

        try:
            
            sock.connect(self.addr)
            sock.shutdown(SHUT_RDWR)
            
            sock.close()

            return True

        except error:

            sock.close()
            return False

    def __int__(self) -> int:
        return self.port
    
    def __repr__(self) -> str:
        return f"Port({self.port})"

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

class URL:

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
        params: dict[str, str] = None, # TODO deprecated - remove later
        *,
        headers: dict[str, str] = None, # TODO deprecated - remove later
        stream: bool = False,
        max_tries: int | None = 1,
        timeout: None|int = 30,
        allow_redirects: bool = True
    ) -> 'Response':
        """requests.get Wrapper"""
        from requests import exceptions
        from ..terminal import Log

        if params: # TODO deprecated - remove later
            self.params = params
        if headers:
            self.headers = headers

        Log.VERB(
            'Requesting Page\n'+ \
            f'{self.furl=}\n'+ \
            f'{self.url=}\n'+ \
            f'{self.params=}\n'+ \
            f'{self.headers=}'
        )

        try:
            return Session(max_tries).get(
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

class FirewallException:

    def __init__(self,
        name: str
    ) -> None:
        """Windows Defender Inbound Exception"""
        self.name: str = name

    def __repr__(self) -> str:
        return f'FirewallException({self.name})'

    @property
    def exists(self) -> bool:
        """Check if this exception exists in Windows Defender"""
        from ..process import RunHidden

        p = RunHidden('netsh', 'advfirewall', 'firewall', 'show', 'rule', f'name={self.name}')

        return ("No rules match the specified criteria." not in p.output())
    
    def delete(self) -> None:
        """Remove this exception from Windows Defender"""
        from ..process import RunHidden

        RunHidden(
            'netsh', 'advfirewall', 'firewall',
            'delete',
            'rule', f'name={self.name}'
        )

    def set(self,
        i: 'int | Path',
        dir: Literal['in', 'out'] = 'in',
        override: bool = False
    ) -> None:
        """
        Add this exception to Windows Defender

        (Deletes & Readds if it already exists)
        """
        from philh_myftp_biz.pc import Path
        from ..process import RunHidden

        if self.exists:
            
            if override:
                self.delete()
            #else:
            #    raise FileExistsError(self)
        
        args = [
            'netsh', 
            'advfirewall', 'firewall',
            'add',
            'rule', f'name={self.name}',
            f'dir={dir}',
            'action=allow',
            'protocol=TCP'
        ]

        if isinstance(i, int):
            args += [f'localport={i}']

        elif isinstance(i, Path):
            args += [f'program={i.wpath}']

        RunHidden(*args)
  