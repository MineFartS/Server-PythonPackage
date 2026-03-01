from typing import Literal, Generator, TYPE_CHECKING, Callable
from functools import partial

if TYPE_CHECKING:
    from qbittorrentapi import Client, TorrentDictionary, TorrentFile
    from selenium.webdriver.remote.webelement import WebElement
    from paramiko.channel import ChannelFile, ChannelStderrFile
    from requests import Response
    from .time import from_stamp
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

class SSH:
    """
    SSH Client

    Wrapper for paramiko.SSHClient
    """

    class Response:

        def __init__(self,
            stdout: 'ChannelFile',
            stderr: 'ChannelStderrFile'
        ) -> None:
            
            self.output: str = stdout.read().decode()
            """stdout"""

            self.error: str = stderr.read().decode()
            """stderr"""

    def __init__(self,
        ip: str,
        username: str,
        password: str,
        timeout: int = None,
        port: int = 22
    ) -> None:
        from paramiko import SSHClient, AutoAddPolicy

        self.__client = SSHClient()

        self.__client.set_missing_host_key_policy(policy=AutoAddPolicy())

        self.__client.connect(
            hostname = ip, 
            port = port, 
            username = username, 
            password = password, 
            timeout = timeout
        )

        self.close: Callable[[], None] = self.__client.close
        """Close the connection to the remote computer"""

    def run(self, command:str) -> SSH.Response:
        """
        Send a command to the remote computer
        """

        # Execute a command
        stdout, stderr = self.__client.exec_command(command)[1:]

        return self.Response(stdout, stderr)

def get(
    url: str,
    params: dict[str, str] = {},
    headers: dict[str, str] = {},
    stream: bool = None
) -> 'Response':
    """
    Wrapper for requests.get
    """
    from .terminal import Log
    from requests import get

    headers['User-Agent'] = 'Mozilla/5.0'
    headers['Accept-Language'] = 'en-US,en;q=0.5'

    Log.VERB(
        f'Requesting Page\n'+ \
        f'{url=}\n'+ \
        f'{params=}\n'+ \
        f'{headers=}'
    )

    return get(
        url = url,
        params = params,
        headers = headers,
        stream = stream
    )

class api:
    """
    Wrappers for several APIs
    """

    class omdb:
        """
        OMDB API

        'https://www.omdbapi.com/{url}'
        """

        __url: str = 'https://www.omdbapi.com/'

        def __init__(self,
            key: int = 0
        ):
            
            match key:

                case 0: self.key = 'dc888719'

                case 1: self.key = '2e0c4a98'

                case _: raise KeyError()

        class Movie:
            Title: str
            Year: int
            Released: 'from_stamp'

        class Show:
            Title: str
            Year: int
            Seasons: dict[str, dict[str, api.omdb.Episode]]

        class Episode:
            Title: str
            Released: 'from_stamp|None'
            Number: int

        def movie(self,
            title: str,
            year: int
        ) -> None | Movie:
            """
            Get details of a movie
            """
            from .time import from_string
            from .json import Dict

            response = get(
                url = self.__url,
                params = {
                    't': title,
                    'y': year,
                    'apikey': self.key
                }                

            )

            r: Dict[str] = Dict(response.json())

            if bool(r['Response']):
                
                if r['Type'] == 'movie':

                    movie = self.Movie()

                    movie.Title = r['Title'] # pyright: ignore[reportAttributeAccessIssue]
                    movie.Year = int(r['Year'])
                    movie.Released = from_string(r['Released'])

                    return movie

        def show(self,
            title: str,
            year: int
        ) -> None | Show:
            """
            Get details of a show
            """
            from .time import from_string
            from .json import Dict

            # Request raw list of seasons
            req = get(
                url = self.__url,
                params = {
                    't': title,
                    'y': year,
                    'apikey': self.key
                }
            )

            # Parse the response
            pres: Dict[str] = Dict(req.json())

            # If an error is given
            if pres['Error']:

                # Raise an error with the given message
                raise ConnectionAbortedError(pres['Error'])

            # If a response of 'series' type is given
            elif pres['Type'] == 'series':

                # Create new 'Show' obj
                show = self.Show()

                #
                show.Seasons = {}

                # Set attributes of 'Show' obj
                show.Title = title
                show.Year = year

                # Iter through all seasons by #
                for s in range(1, int(pres['totalSeasons'])+1):

                    show.Seasons[f'{s:02d}'] = {}

                    # Request season details and parse response
                    pres2: dict[str, str] = get(
                        url = self.__url,
                        params = {
                            't': title,
                            'y': year,
                            'Season': s,
                            'apikey': self.key
                        }
                    ).json()

                    # Iterate through the episodes in the season details
                    for e in pres2['Episodes']:

                        # Create new 'Episode' obj
                        episode = self.Episode()

                        # Set attributes of 'Episode' obj
                        episode.Title = e['Title']
                        episode.Number = int(e['Episode'])
                        
                        # If the show has a release date, then parse the date
                        try:
                            episode.Released = from_string(e['Released'])
                        except TypeError:
                            episode.Released = None

                        show.Seasons [f'{s:02d}'] [e['Episode'].zfill(2)] = episode

                # Return the 'Show' obj
                return show

    class qBitTorrent:
        """
        Client for qBitTorrent Web Server
        """

        class File:
            """
            Downloading Torrent File
            """

            def __init__(self,
                torrent: 'TorrentDictionary',
                file: 'TorrentFile'
            ) -> None:
                from .pc import Path
                
                self.path = Path(f'{torrent.save_path}/{file.name}')
                """Download Path"""
                
                self.size: float = file.size
                """File Size"""

                self.title: str = file.name[file.name.find('/')+1:]
                """File Name"""

                self.__id: str = file.id
                """File ID"""

                self.__torrent = torrent
                """Torrent"""

            def _file(self) -> 'TorrentFile':
                return self.__torrent.files[self.__id]

            def progress(self) -> float:
                return self._file().progress

            def start(self,
                force: bool = False
            ):
                """
                Start downloading the file
                """
                from .terminal import Log

                Log.VERB(f'Downloading File: {force=} | {self}]')

                self.__torrent.file_priority(
                    file_ids = self.__id,
                    priority = (7 if force else 1)
                )

            def enabled(self) -> bool:
                """
                """

                priority: int = self._file().priority

                return (priority > 0)

            def downloading(self) -> bool:
                """
                """

                return (self.enabled() and (not self.finished()))

            def stop(self) -> None:
                """
                Stop downloading the file

                Ignores error if the magnet is not found
                """
                from qbittorrentapi.exceptions import NotFound404Error
                from .terminal import Log

                Log.VERB(f'Stopping File: {self}')

                try:
                    self.__torrent.file_priority(
                        file_ids = self.__id,
                        priority = 0
                    )
                except NotFound404Error:
                    pass

            def finished(self) -> bool:
                """
                Check if the file is finished downloading
                """

                return (self.progress() == 1)

            def __repr__(self) -> str:
                from .text import abbreviate
                from .classtools import loc

                return f"<File '{abbreviate(num=30, string=self.title)}' @{loc(obj=self)}>"

        def __init__(self,
            host: str,
            username: str,
            password: str,
            port: int = 8080,
            timeout: int = 3600 # 1 hour
        ) -> None:
            from qbittorrentapi import Client
            from .terminal import Log

            Log.VERB(
                f'Connecting to qBitTorrentAPI\n'+ \
                f'{host=} | {port=}\n'+ \
                f'{username=}\n'+ \
                f'{timeout=}'
            )

            self.host: str = host
            self.port: int = port
            self.timeout: int = timeout

            self._rclient = Client(
                host = host,
                port = port,
                username = username,
                password = password,
                VERIFY_WEBUI_CERTIFICATE = False,
                REQUESTS_ARGS = {'timeout': (timeout, timeout)}
            )

        def _client(self) -> 'Client':
            """
            Wait for server connection, then returns qbittorrentapi.Client
            """
            from qbittorrentapi.exceptions import LoginFailed, Forbidden403Error, APIConnectionError
            from .time import Stopwatch
            from .terminal import Log

            sw = Stopwatch()
            sw.start()

            while True:

                try:

                    self._rclient.torrents_info()

                    return self._rclient
                
                except LoginFailed, Forbidden403Error, APIConnectionError:
                    Log.WARN('qBitTorrentAPI Connection Error')

                if sw.elapsed() >= self.timeout:
                    raise TimeoutError('qBitTorrentAPI Connection Timed Out')

        def _get(self,
            magnet: Magnet
        ):

            for t in self._client().torrents_info():
                
                #
                if t.hash == magnet.hash:

                    return t

        def connected(self) -> bool:
            """
            Check if qBitTorrent is connected to the internet
            """

            tinfo = self._client().transfer.info()

            conn_status = tinfo.connection_status

            return (conn_status == 'connected')

        def start(self,
            magnet: 'Magnet',
            path: 'str|Path' = None
        ) -> None:
            """
            Start Downloading a Magnet
            """
            from .terminal import Log

            t = self._get(magnet)

            Log.VERB(
                f'Starting\n'+ \
                f'{magnet=}\n'+ \
                f'{path=}'
            )

            if path:
                path = str(path)

            if t:
                t.start()
            
            else:
                self._client().torrents_add(
                    urls = magnet.url,
                    save_path = path
                )

        def reannounce(self,
            magnet: 'Magnet'
        ) -> None:
            """
            """
            from .terminal import Log

            Log.VERB(f'Reannouncing: {magnet=}')

            t = self._get(magnet)

            if t:

                t.reannounce()

        def restart(self,
            magnet: 'Magnet'
        ) -> None:
            """
            Restart Downloading a Magnet
            """
            from .terminal import Log

            Log.VERB(f'Restarting: {magnet=}')

            self.stop(magnet)
            self.start(magnet)

        def files(self,
            magnet: 'Magnet'
        ) -> list[api.qBitTorrent.File]:
            """
            List all files in Magnet Download

            Waits for at least one file to be found before returning
            """
            from .time import Stopwatch
            from .terminal import Log

            Log.VERB(f'Scanning Files: {magnet=}')

            sw = Stopwatch()
            sw.start()

            t = self._get(magnet)

            if t:

                t.setForceStart(True)

                #
                while len(t.files) == 0:

                    if sw >= self.timeout:

                        raise TimeoutError()

                t.setForceStart(False)

                return [self.File(t,f) for f in t.files]
            
            else:
                return []

        def stop(self,
            magnet: 'Magnet',
            rm_files: bool = True
        ) -> None:
            """
            Stop downloading a Magnet
            """
            from .terminal import Log
            
            t = self._get(magnet=magnet)

            Log.VERB(f'Stopping: {rm_files=} | {magnet=}')

            t.delete(delete_files=rm_files)

            return

        def clear(self,
            rm_files: bool = True,
            filter_func: Callable[['TorrentDictionary'], bool] = lambda t: True
        ) -> None:
            """
            Remove all Magnets from the download queue
            """
            from .text import from_function
            from .terminal import Log

            Log.VERB(
                f'Clearing Download Queue:\n'+ \
                f'{rm_files=}\n'+ \
                'func='+from_function(filter_func)
            )

            for torrent in self._client().torrents_info():

                if filter_func(torrent):
                
                    Log.VERB(f'Deleting Queue Item: {rm_files=} | {torrent.name=}')
                    
                    torrent.delete(rm_files)

        def finished(self,
            magnet: 'Magnet'
        ) -> None | bool:
            """
            Check if a magnet is finished downloading
            """
            
            t = self._get(magnet)
            
            if t:
                return (t.state_enum.is_uploading or t.state_enum.is_complete)

        def errored(self,
            magnet: 'Magnet'
        ) -> None | bool:
            """
            Check if a magnet is errored
            """

            t = self._get(magnet)

            if t:
                return t.state_enum.is_errored

        def downloading(self,
            magnet: 'Magnet'
        ) -> None | bool:
            """
            Check if a magnet is downloading
            """
                        
            t = self._get(magnet)
            
            if t:
                return t.state_enum.is_downloading

        def exists(self,
            magnet: 'Magnet'
        ) -> bool:
            """
            Check if a magnet is in the download queue
            """
            
            t = self._get(magnet)
            
            return (t != None)

        def stalled(self,
            magnet: 'Magnet'
        ) -> None | bool:
            """
            Check if a magnet is stalled
            """
                        
            t = self._get(magnet)
            
            if t:
                return (t.state_enum.value == 'stalledDL')

        def randomize_port(self) -> None:
            from random import randint
            
            # Update preference
            self._client().app_setPreferences(preferences={
                'listen_port': randint(a=10000, b=60000)
            })

    class thePirateBay:
        """
        thePirateBay

        'https://thepiratebay.org/'
        """
        
        def __init__(self,
            url: Literal[
                "thepiratebay11.com",
                "thepiratebay10.info",
                "thepiratebay7.com",
                "thepiratebay0.org",
                "thehiddenbay.com",
                "piratebay.live",
                "tpb.party"
            ] = "thepiratebay0.org",
            driver: Driver = None,
            qbit: 'api.qBitTorrent' = None
        ) -> None:
            
            self.__url = url
            """tpb mirror url"""

            self.__qbit = qbit
            """qBitTorrent Session"""
            
            if driver:
                self.__driver = driver
            else:
                self.__driver = Driver()

        def search(self,
            query: str
        ) -> None | Generator[Magnet]:
            """
            Search thePirateBay for magnets

            EXAMPLE:
            for magnet in thePirateBay.search('term'):
                magnet
            """
            from .db import Size

            # Remove all "." & "'" from query
            query = query.replace('.', '').replace("'", '')

            # Open the search in a url
            self.__driver.open(
                url = f'https://{self.__url}/search/{query}/1/99/0'
            )

            try:

                # Set driver var 'lines' to a list of lines
                self.__driver.run(code="window.lines = document.getElementById('searchResult').children[1].children")

                # Iter from 0 to # of lines
                for x in range(0, self.__driver.run('return lines.length')):

                    # Yield a magnet instance
                    yield Magnet(

                        # Raw Tttle
                        title = self.__driver.run(f"return lines[{x}].children[1].textContent"),

                        # Num of Seeders
                        seeders = int(self.__driver.run(f"return lines[{x}].children[5].textContent")),

                        # Num of leechers
                        leechers = int(self.__driver.run(f"return lines[{x}].children[6].textContent")),

                        # Magnet URL
                        url = self.__driver.run(f"return lines[{x}].children[3].children[0].children[0].href"),
                        
                        # Download Size
                        size = Size.to_bytes(self.__driver.run(f"return lines[{x}].children[4].textContent")),

                        # qBitTorrent Session
                        qbit = self.__qbit

                    )
            
            except RuntimeError, KeyError:
                pass

class Magnet(api.qBitTorrent):
    """
    Handler for MAGNET URLs
    """

    __qualities: dict[str, int] = {
        'hdtv': 0,
        'tvrip': 0,
        '2160p': 2160,
        '1440p': 1440,
        '1080p': 1080,
        '720p': 720,
        '480p': 480,
        '360p': 360,
        '4K': 2160
    }
    """
    QUALITY LOOKUP TABLE

    Find quality in magnet title
    """

    def __init__(self,
        title: str = '',
        seeders: int = -1,
        leechers: int = -1,
        url: str = '',
        size: str = -1,
        qbit: api.qBitTorrent = None
    ) -> None:
        from urllib.parse import urlparse, parse_qs
        from functools import partial
        from inspect import signature

        # Get the value of the 'xt' parameter (it's a list, so take the first element)
        XT: str = parse_qs(urlparse(url).query)['xt'][0]
        
        # The hash follows 'urn:btih:' or 'urn:btmh:'
        if XT.startswith('urn:btih:'):
            self.hash = XT[len('urn:btih:'):].lower()
        
        elif XT.startswith('urn:btmh:'): # for v2 magnets
            self.hash = XT[len('urn:btmh:'):].lower()
            
        self.title: str = title.lower()
        self.leechers: int = leechers
        self.seeders: int = seeders
        self.size: str = size
        self.url: str = url

        self.quality = 0
        for term in self.__qualities:
            if term in self.title:
                self.quality: int = self.__qualities[term]

        if qbit:
            for name in ['_rclient', 'timeout']:
                setattr(
                    self, name,
                    getattr(qbit, name)
                )

        for name, value in vars(api.qBitTorrent).items():

            CALLABLE = callable(value)

            PUBLIC = ('_' not in name)

            MAGNETPARAM = (CALLABLE and ('magnet' in signature(value).parameters))

            if CALLABLE and PUBLIC and MAGNETPARAM:

                setattr(
                    self, name,
                    partial(value, self=self, magnet=self)
                )

    def __repr__(self) -> str:
        from .classtools import loc
        from .text import abbr

        return f"<Magnet '{abbr(30, self.title.strip())}' @{loc(self)}>"

class Driver:
    """
    Firefox Web Driver
    
    Wrapper for FireFox Selenium Session
    """

    URL: str|None
    """URL of the Current Page"""

    HTML: str|None
    """HTML of the Current Page"""

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
        Sleeper(func=self.close())

    def reload(self) -> None:
        """Reload the Current Page"""
        from .terminal import Log

        Log.VERB(f'Reloading Page: {self.current_url=}')

        self._drvr.refresh()

    def run(self, code:str):
        """Run JavaScript Code on the Current Page"""
        from .terminal import Log
        from selenium.common.exceptions import JavascriptException

        Log.VERB(
            f'Executing JavaScript\n'+ \
            f'{self.current_url=}\n'+ \
            f'{code=}'
        )

        try:

            response = self._drvr.execute_script(code)

            Log.VERB(
                f'JavaScript Executed\n'+ \
                f'{response=}'
            )

            return response
        
        except JavascriptException as e:

            # Truncate the Error Message
            mess: str = e.msg
            mess = mess[mess.find(':')+2:]
            mess = mess[:mess.find('\nStacktrace:')]

            raise RuntimeError(mess) from None

    def element(self,
        by: Literal['class', 'id', 'xpath', 'name', 'attr'],
        name: str,
        wait: bool = True
    ) -> list['WebElement']:
        """
        Get List of Elements by query
        """
        from selenium.webdriver.common.by import By
        from .terminal import Log

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

        while True:

            elements: list['WebElement'] = self._drvr.find_elements(by=BY, value=name)

            # If at least 1 element was found
            if (len(elements) > 0) or (not wait):

                Log.VERB(f"Found Elements: {elements=}")

                return elements

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

        # Open the url
        while True:
            try:
                self._drvr.get(url=url)
                return
            except WebDriverException, ReadTimeoutError:
                Log.WARN('Failed to open url', exc_info=True)

    def close(self) -> None:
        """
        Close the Session
        """
        from selenium.common.exceptions import InvalidSessionIdException
        from .terminal import Log

        Log.VERB('Closing Session')

        try:
            # Exit Session
            self._drvr.quit()
        except InvalidSessionIdException:
            pass

    def __getattr__(self, name:str):
        from selenium.common.exceptions import WebDriverException

        match name:

            case 'HTML':
                try:
                    return self._drvr.page_source
                except WebDriverException:
                    return None
                
            case 'URL':
                try:
                    return self._drvr.current_url
                except WebDriverException:
                    return None
            
            case _:

                return self.__dict__[name]

def download(
    url: str,
    path: 'Path',
    show_progress: bool = True
) -> None:
    """
    Download file to disk
    """
    from urllib.request import urlretrieve
    from tqdm import tqdm
    
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

        if self.exists():
            
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
  