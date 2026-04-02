from typing import Literal, TYPE_CHECKING
from .functools import single_use
from functools import partial

if TYPE_CHECKING:
    from selenium.webdriver.remote.webelement import WebElement
    from requests import Response
    from .pc import Path

#=========================================
# Temporary Backwards Compatibility
# TODO: Update all references to new function

def get(url:str, *args, **kwargs): # pyright: ignore[reportMissingParameterType]
    return URL(url).get(*args, **kwargs)

def ping(addr:str, *args, **kwargs): # pyright: ignore[reportMissingParameterType]
    return URL(addr).online

def download(url:str, *args, **kwargs): # pyright: ignore[reportMissingParameterType]
    return URL(url).download(*args, **kwargs)
#=========================================

class IP:

    def LAN() -> str:
        from socket import gethostname, gethostbyname

        return gethostbyname(gethostname())
    
    def WAN() -> str:
        return get('https://api.ipify.org').text

is_online: partial[bool] = partial(ping, '1.1.1.1')
"""Check if the local computer is connected to the internet"""

class Port:
    """
    Details of a port on a network device
    """

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
    from .num import maxint

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
        from urllib.parse import urlparse

        self.url = url

        self._parsed = urlparse(url)
        self.netloc = self._parsed.netloc

        if self.netloc:
            self.addr = self.netloc
        else:
            self.addr = url

    @property
    def _stream(self):
        return self.get(stream=True)

    def download(self,
        path: 'Path',
        show_progress:bool = None # TODO: Fix all references, then remove
    ) -> None:
        """Download file to disk"""
        from .terminal import Log
        from . import VERBOSE
        from tqdm import tqdm

        Log.VERB(f'Downloading File:\nurl={self.url}\n{path=}')

        r = self._stream

        file = path.open(mode='wb')

        if VERBOSE:
            pbar = tqdm(
                total = self.size, # Total Download Size
                unit = "B",
                unit_scale = True
            )

        # Iter through all data in stream
        for data in r.iter_content(chunk_size=1024):

            if VERBOSE:
                pbar.update(n=len(data)) # pyright: ignore[reportPossiblyUnboundVariable]

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
        params: dict[str, str] = {},
        headers: dict[str, str] = {},
        stream: bool = None,
        max_tries: int = None,
        timeout: None|int = None,
        method: Literal['GET', 'POST'] = 'GET'
    ) -> 'Response':
        """requests.get Wrapper"""
        from .terminal import Log

        headers['User-Agent'] = 'Mozilla/5.0'
        headers['Accept-Language'] = 'en-US,en;q=0.5'

        Log.VERB(
            f'Requesting Page\n'+ \
            f'url={self.url}\n'+ \
            f'{params=}\n'+ \
            f'{headers=}'
        )

        session = Session(max_tries)

        return getattr(session, method.lower())(
            url = self.url,
            params = params,
            headers = headers,
            stream = stream,
            timeout = timeout
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

    def cache(self, path:'Path') -> None:

        if (not path.exists) or (path.size != self.size):

            self.download(path)

class Driver:
    """
    Firefox Web Driver
    
    Wrapper for FireFox Selenium Session
    """

    def __init__(self,
        headless: bool = True,
        eager: bool = False,
        timeout: int = 300
    ) -> None:
        from selenium.webdriver import FirefoxOptions, Firefox
        from selenium.webdriver.firefox.options import Options
        from .process import SysTask, Sleeper
        from .terminal import Log

        Log.VERB(
            f'Starting Session\n'+ \
            f'{headless=}\n'+ \
            f'{eager=}\n'+ \
            f'{timeout=}'
        )

        options: Options = FirefoxOptions()

        if eager:
            options.page_load_strategy = 'eager'

        if headless:
            options.add_argument("--headless")

        # Start Chrome Session with options
        self._drvr = Firefox(options=options)

        self.Task = SysTask(self._drvr.service.process.pid)

        # Set Timeouts
        self._drvr.command_executor.set_timeout(timeout)
        self._drvr.set_page_load_timeout(time_to_wait=timeout)
        self._drvr.set_script_timeout(time_to_wait=timeout)

        # Close the session if the main thread ends
        Sleeper(func=self.close)

    def reload(self) -> None:
        """Reload the Current Page"""
        from .terminal import Log

        Log.VERB(f'Reloading Page: {self.URL=}')

        self._drvr.refresh()

    def run(self, code:str):
        """Run JavaScript Code on the Current Page"""
        from selenium.common.exceptions import JavascriptException
        from .terminal import Log

        try:

            response = self._drvr.execute_script(code)

            Log.VERB(
                f'JavaScript Executed\n'+ \
                f'{self.URL=}\n'+ \
                f'{code=}\n'+ \
                f'{response=}'
            )

            return response
        
        except JavascriptException as e:

            raise RuntimeError(e.msg) from None

    def element(self,
        by: Literal['class', 'id', 'xpath', 'name', 'attr'],
        name: str,
        timeout: int = 30
    ) -> list['WebElement']:
        """Get List of Elements by query"""
        from selenium.webdriver.common.by import By
        from .terminal import Log
        from .time import Stopwatch

        sw = Stopwatch().start()

        Log.VERB(f"Finding Element: {by=} | {name=}")

        match by.lower():

            case 'class':

                if isinstance(name, list):
                    name = '.'.join(name)

                BY = By.CLASS_NAME

            case 'id':
                BY = By.ID

            case 'xpath':
                BY = By.XPATH

            case 'name':
                BY = By.NAME

            case 'attr':
                name = f"a[{name}']"
                BY = By.CSS_SELECTOR

            case _:
                raise TypeError(f'"{by}" is an invalid method')

        while sw.elapsed < timeout:

            elements: list['WebElement'] = self._drvr.find_elements(by=BY, value=name)

            # If at least 1 element was found
            if len(elements) > 0:

                Log.VERB(f"Found Elements: {elements=}")

                return elements
            
        return []

    def open(self,
        url: str
    ) -> None:
        """
        Open a url

        Waits for page to fully load
        """
        from selenium.common.exceptions import WebDriverException
        from urllib3.exceptions import ReadTimeoutError
        from .terminal import Log

        Log.VERB(f"Opening Page: {url=}")

        # Switch to the first tab
        handle = self._drvr.window_handles[0]
        self._drvr.switch_to.window(handle)

        # Open the url
        while True:
            try:
                self._drvr.get(url=url)
                return
            except WebDriverException, ReadTimeoutError:
                Log.WARN('Failed to open url', exc_info=True)

    @single_use
    def close(self) -> None:
        """Close the Session"""
        from selenium.common.exceptions import InvalidSessionIdException
        from .terminal import Log

        Log.VERB('Closing Session')

        try:
            # Exit Session
            self._drvr.quit()
        except InvalidSessionIdException:
            pass

    @property
    def HTML(self) -> str | None:
        """HTML of the Current Page"""
        from selenium.common.exceptions import WebDriverException
        
        try:
            return self._drvr.page_source
        except WebDriverException:
            pass
        
    @property
    def URL(self) -> str | None:
        """URL of the Current Page"""
        from selenium.common.exceptions import WebDriverException

        try:
            return self._drvr.current_url
        except WebDriverException:
            pass

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
        from .process import RunHidden

        p = RunHidden(args=['netsh', 'advfirewall', 'firewall', 'show', 'rule', f'name={self.name}'])

        return ("No rules match the specified criteria." not in p.output())
    
    def delete(self) -> None:
        """Remove this exception from Windows Defender"""
        from .process import RunHidden

        RunHidden([
            'netsh', 'advfirewall', 'firewall',
            'delete',
            'rule', f'name={self.name}'
        ])

    def set(self,
        i: 'int | Path',
        dir: Literal['in', 'out'] = 'in',
        override: bool = True
    ) -> None:
        """
        Add this exception to Windows Defender

        (Deletes & Readds if it already exists)
        """
        from philh_myftp_biz.pc import Path
        from .process import RunHidden

        if self.exists:
            
            if override:
                self.delete()
            else:
                raise FileExistsError(self)
        
        args = [
            'netsh', 
            'advfirewall', 'firewall',
            'add',
            'rule', f'name={self.name}',
            f'dir={dir}',
            'action=allow'
        ]

        if isinstance(i, int):
            args += ['protocol=TCP']

        elif isinstance(i, Path):
            args += [f'program={i.wpath}']

        RunHidden(args)
  