from typing import Literal, TYPE_CHECKING
from .functools import single_use
from functools import partial

if TYPE_CHECKING:
    from selenium.webdriver.remote.webelement import WebElement
    from requests import Response
    from .pc import Path

class IP:

    def LAN() -> str:
        from socket import gethostname, gethostbyname

        return gethostbyname(gethostname())
    
    def WAN() -> str:
        return get('https://api.ipify.org').text

def ping(
    addr: str,
    timeout: int = 3
) -> bool:
    """
    Ping a network address

    Returns true if ping reached destination
    """
    from urllib.parse import urlparse
    from ping3 import ping

    # Parse the given address
    parsed = urlparse(addr)

    # If the parser finds a network location
    if parsed.netloc:

        # Set the address to the network location
        addr = parsed.netloc

    try:

        # Ping the address
        p = ping(
            dest_addr = addr,
            timeout = timeout
        )

        # Return true/false if it went through
        return bool(p)
    
    except OSError:
        return False

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

def get(
    url: str,
    params: dict[str, str] = {},
    headers: dict[str, str] = {},
    stream: bool = None,
    max_tries: int = None,
    timeout: None|int = None,
    method: Literal['GET', 'POST'] = 'GET'
) -> 'Response':
    """
    Wrapper for requests.get
    """
    from requests.adapters import HTTPAdapter, Retry
    from requests import Session
    from .terminal import Log
    from .num import maxint    

    headers['User-Agent'] = 'Mozilla/5.0'
    headers['Accept-Language'] = 'en-US,en;q=0.5'

    Log.VERB(
        f'Requesting Page\n'+ \
        f'{url=}\n'+ \
        f'{params=}\n'+ \
        f'{headers=}'
    )

    retry_strategy = Retry(
        total = (max_tries if max_tries else maxint),
        backoff_factor = 1,
        status_forcelist = list(range(400, 600)),
        allowed_methods = ["GET", "POST"]
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)

    session = Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return getattr(session, method.lower())(
        url = url,
        params = params,
        headers = headers,
        stream = stream,
        timeout = timeout
    )

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

def download(
    url: str,
    path: 'Path',
    show_progress: bool = True
) -> None:
    """Download file to disk"""
    from urllib.request import urlretrieve
    from .terminal import Log
    from tqdm import tqdm

    Log.VERB(f'Downloading File:\n{url=}\n{path=}')
    
    # If show_progress is True
    if show_progress:

        # Stream the url
        r = get(
            url = url,
            stream = True
        )

        # Open the destination file
        file = path.open(mode='wb')

        # Create a new progress bar
        pbar = tqdm(
            total = int(r.headers.get("content-length", 0)), # Total Download Size
            unit = "B",
            unit_scale = True
        )

        # Iter through all data in stream
        for data in r.iter_content(chunk_size=1024):

            # Update the progress bar
            pbar.update(n=len(data))

            # Write the data to the dest file
            file.write(data)

    else:

        # Download directly to the desination file
        urlretrieve(url=url, filename=str(path))

class FirewallException:

    def __init__(self,
        name: str
    ) -> None:
        """
        Windows Defender Inbound Port Exception
        """
        self.name: str = name

    def __repr__(self) -> str:
        return f'FirewallException({self.name})'

    @property
    def exists(self) -> bool:
        """
        Check if this exception exists in Windows Defender
        """
        from .process import RunHidden

        p = RunHidden(args=['netsh', 'advfirewall', 'firewall', 'show', 'rule', f'name={self.name}'])

        return ("No rules match the specified criteria." not in p.output())
    
    def delete(self) -> None:
        """
        Remove this exception from Windows Defender
        """
        from .process import RunHidden

        RunHidden([
            'netsh', 'advfirewall', 'firewall',
            'delete',
            'rule', f'name={self.name}'
        ])

    def set(self,
        port: int,
        override: bool = True
    ) -> None:
        """
        Add this exception to Windows Defender

        (Deletes & Readds if it already exists)
        """
        from .process import RunHidden

        if self.exists:
            
            if override:
                self.delete()
            else:
                raise FileExistsError(self)

        RunHidden([
            'netsh', 'advfirewall', 'firewall',
            'add',
            'rule', f'name={self.name}',
            'dir=in', 
            'action=allow',
            'protocol=TCP',
            f'localport={port}'
        ])
  