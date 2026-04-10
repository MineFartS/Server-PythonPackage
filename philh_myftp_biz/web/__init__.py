from typing import Literal, TYPE_CHECKING
from ..functools import single_use
from functools import partial

if TYPE_CHECKING:
    from selenium.webdriver.remote.webelement import WebElement
    from requests import Response
    from ..pc import Path

class IP:

    def LAN() -> str:
        from socket import gethostname, gethostbyname

        return gethostbyname(gethostname())
    
    def WAN() -> str:
        return get('https://api.ipify.org').text

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

class URL:

    def __init__(self, url:str) -> None:
        from urllib.parse import urlparse, parse_qsl

        self.url = url.split('?')[0]

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
        return URL(self.furl)

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
        
        url = self.url

        if url[-1] != '/':
            url += '/'

        # TODO add logic for parameters

        url += name

        return URL(url)

    @property
    def stream(self):
        return self.get(stream=True)

    @property
    def content(self):
        return self.get().content

    @property
    def json(self):
        return self.get().json()

    def download(self,
        path: 'Path'
    ) -> None:
        """Download file to disk"""
        from ..classtools import Absorber
        from ..terminal import Log
        from .. import VERBOSE
        from tqdm import tqdm

        Log.VERB(f'Downloading File:\nurl={self.url}\n{path=}')

        r = self.stream

        file = path.open(mode='wb')

        if VERBOSE:
            pbar = tqdm(
                total = self.size, # Total Download Size
                unit = "B",
                unit_scale = True
            )
            chunk_size = 1024
        else:
            pbar = Absorber()
            chunk_size = None

        # Iter through all data in stream
        for data in r.iter_content(chunk_size):

            pbar.update(n=len(data))

            # Write the data to the dest file
            file.write(data)

    @property
    def size(self) -> int:
        from requests import head
        
        r = head(
            self.url, 
            allow_redirects = True
        )

        return int(r.headers.get('Content-Length', 0))

    def get(self,
        params: dict[str, str] = {}, # TODO deprecated - remove later
        *,
        headers: dict[str, str] = {},
        stream: bool = None,
        max_tries: int = None,
        timeout: None|int = None,
        allow_redirects: bool = True
    ) -> 'Response':
        """requests.get Wrapper"""
        from ..terminal import Log

        if len(params) > 0: # TODO deprecated - remove later
            self.params = params

        Log.VERB(
            f'Requesting Page\n'+ \
            f'url={self.url}\n'+ \
            f'{self.params=}\n'+ \
            f'{headers=}'
        )

        return Session(max_tries).get(
            url = self.url,
            params = self.params,
            headers = headers,
            stream = stream,
            timeout = timeout,
            allow_redirects = allow_redirects
        )

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

        p = RunHidden(args=['netsh', 'advfirewall', 'firewall', 'show', 'rule', f'name={self.name}'])

        return ("No rules match the specified criteria." not in p.output())
    
    def delete(self) -> None:
        """Remove this exception from Windows Defender"""
        from ..process import RunHidden

        RunHidden([
            'netsh', 'advfirewall', 'firewall',
            'delete',
            'rule', f'name={self.name}'
        ])

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

        RunHidden(args)
  