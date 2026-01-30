from typing import Literal, Self, Generator, TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from qbittorrentapi import Client, TorrentDictionary, TorrentFile
    from paramiko.channel import ChannelFile, ChannelStderrFile
    from requests import Response
    from bs4 import BeautifulSoup
    from .pc import Path
    from .time import from_stamp

def IP(
    method: Literal['local', 'public'] = 'local'
) -> str | None:
    """
    Get the IP Address of the local computer
    """
    from socket import gethostname, gethostbyname

    if method == 'local':
        return gethostbyname(gethostname())
    
    elif online():
        return get('https://api.ipify.org').text

online = lambda: ping('1.1.1.1')
"""Check if the local computer is connected to the internet"""

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

class Port:
    """
    Details of a port on a network device
    """

    def __init__(self,
        host: str,
        port: int
    ):
        from socket import error, SHUT_RDWR
        from quicksocketpy import socket
        self.port = port

        s = socket()

        try:
            s.connect((host, port))
            s.shutdown(SHUT_RDWR)
            self.listening = True
            """Port is listening"""
            
        except error:
            self.listening = False
            """Port is listening"""
        
        finally:
            s.close()

    def __int__(self) -> int:
        return self.port

def find_open_port(min:int, max:int) -> None | int:
    """
    Find an open port in a range on a network device
    """

    for x in range(min, max+1):
        
        port = Port(IP(), x)
        
        if not port.listening:
            return int(port)

class ssh:
    """
    SSH Client

    Wrapper for paramiko.SSHClient
    """

    class __Response:

        def __init__(self,
            stdout: 'ChannelFile',
            stderr: 'ChannelStderrFile'
        ):
            self.output = stdout.read().decode()
            """stdout"""

            self.error = stderr.read().decode()
            """stderr"""

    def __init__(self,
        ip: str,
        username: str,
        password: str,
        timeout: int = None,
        port: int = 22
    ):
        from paramiko import SSHClient, AutoAddPolicy

        self.__client = SSHClient()
        self.__client.set_missing_host_key_policy(AutoAddPolicy())
        self.__client.connect(ip, port, username, password, timeout=timeout)

        self.close = self.__client.close
        """Close the connection to the remote computer"""

    def run(self, command:str) -> __Response:
        """
        Send a command to the remote computer
        """

        # Execute a command
        stdout, stderr = self.__client.exec_command(command)[1:]

        return self.__Response(stdout, stderr)

def get(
    url: str,
    params: dict = {},
    headers: dict = {},
    stream: bool = None,
    cookies = None
) -> 'Response':
    """
    Wrapper for requests.get
    """
    from requests.exceptions import ConnectionError
    from .terminal import Log
    from requests import get

    headers['User-Agent'] = 'Mozilla/5.0'
    headers['Accept-Language'] = 'en-US,en;q=0.5'

    Log.VERB(f'Requesting Page: {url=} | {params=} | {headers=}')

    # Iter until interrupted
    while True:

        try:

            return get(
                url = url,
                params = params,
                headers = headers,
                stream = stream,
                cookies = cookies
            )
        
        except ConnectionError:
            Log.WARN('Retrying Request', exc_info=True)

class api:
    """
    Wrappers for several APIs
    """

    class omdb:
        """
        OMDB API

        'https://www.omdbapi.com/{url}'
        """

        __url = 'https://www.omdbapi.com/'

        def __init__(self,
            key: int = 0
        ):
            
            match key:

                case 0: self.key = 'dc888719'

                case 1: self.key = '2e0c4a98'

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

                    movie.Title = r['Title']
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

    def numista(url:str='', params:list=[]):
        """
        Numista API

        'https://api.numista.com/v3/{url}'
        """
        return get(
            url = f'https://api.numista.com/v3/{url}',
            params = params,
            headers = {'Numista-API-Key': 'KzxGDZXGQ9aOQQHwnZSSDoj3S8dGcmJO9SLXxYk1'},
        ).json()
    
    def mojang(url:str='', params:list=[]):
        """
        Mojang API

        'https://api.mojang.com/{url}'
        """
        return get(
            url = f'https://api.mojang.com/{url}',
            params = params
        ).json()
    
    def geysermc(url:str='', params:list=[]):
        """
        GeyserMC API

        'https://api.geysermc.org/v2/{url}'        
        """
        return get(
            url = f'https://api.geysermc.org/v2/{url}',
            params = params
        ).json()

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
            ):
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
                prioritize: bool = False
            ):
                """
                Start downloading the file
                """
                from .terminal import Log

                Log.VERB(f'Downloading File: {prioritize=} | {self}]')

                self.__torrent.file_priority(
                    file_ids = self.__id,
                    priority = (7 if prioritize else 1)
                )

            def stop(self):
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

            def __str__(self):
                from .text import abbreviate
                from .classOBJ import loc

                return f"<File '{abbreviate(30, self.title)}' @{loc(self)}>"

        def __init__(self,
            host: str,
            username: str,
            password: str,
            port: int = 8080,
            timeout: int = 3600 # 1 hour
        ):
            from qbittorrentapi import Client
            from .classOBJ import path
            from .terminal import Log

            Log.VERB(f'Connecting to qBitTorrentAPI: {host=} {port=} | {username=} | {timeout=}')

            # if the host is not a string
            if not isinstance(host, str):
                raise TypeError(path(host))

            self.host = host
            self.port = port
            self.timeout = timeout

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
            from .terminal import Log

            while True:

                try:
                    self._rclient.torrents_info()
                    return self._rclient
                
                except LoginFailed, Forbidden403Error, APIConnectionError:
                    Log.WARN('qBitTorrentAPI Connection Error')

        def _get(self,
            magnet: Magnet
        ):
            for t in self._client().torrents_info():
                
                #
                if magnet.url in t.tags:

                    return t

        def start(self,
            magnet: 'Magnet',
            path: 'Path' = None
        ) -> None:
            """
            Start Downloading a Magnet
            """
            from .terminal import Log

            t = self._get(magnet)

            Log.VERB(f'Starting: {repr(magnet)=} | {str(path)=}')

            if t:

                t.start()

                self.reannounce(magnet=magnet)
            
            else:
                self._client().torrents_add(
                    urls = [magnet.url],
                    save_path = str(path),
                    tags = magnet.url
                )

        def reannounce(self,
            magnet: 'Magnet'
        ) -> None:
            """
            """
            from .terminal import Log

            Log.VERB(f'Reannouncing: {repr(magnet)=}')

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

            Log.VERB(f'Restarting: {repr(magnet)=}')

            self.stop(magnet)
            self.start(magnet)

        def files(self,
            magnet: 'Magnet'            
        ) -> Generator[File]:
            """
            List all files in Magnet Download

            Waits for at least one file to be found before returning

            EXAMPLE:

            qbt = qBitTorrent(*args)

            for file in qbit.files():
            
                file['path'] # Path of the downloaded file
                file['size'] # Full File Size
            
            """
            from .time import Stopwatch
            from .terminal import Log
            from time import sleep

            Log.VERB(f'Scanning Files: {repr(magnet)=}')

            sw = Stopwatch()
            sw.start()

            t = self._get(magnet)

            if t:

                t.setForceStart(True)

                #
                while len(t.files) == 0:

                    sleep(1)
                    
                    if sw >= self.timeout:
                        raise TimeoutError()
                    
                    self.reannounce(magnet=magnet)

                t.setForceStart(False)

                for f in t.files:

                    yield self.File(t, f)

        def stop(self,
            magnet: 'Magnet',
            rm_files: bool = True
        ) -> None:
            """
            Stop downloading a Magnet
            """
            from .terminal import Log
            
            t = self._get(magnet)

            Log.VERB(f'Stopping: {rm_files=} | {repr(magnet)=}')

            t.delete(rm_files)

            return

        def clear(self,
            rm_files: bool = True
        ) -> None:
            """
            Remove all Magnets from the download queue
            """
            from .terminal import Log

            Log.VERB(f'Clearing Download Queue: {rm_files=}')

            for torrent in self._client().torrents_info():
                
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
        ):
            
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
            from .terminal import Log
            from .db import Size

            # Remove all "." & "'" from query
            query = query.replace('.', '').replace("'", '')

            # Open the search in a url
            self.__driver.open(
                url = f'https://{self.__url}/search/{query}/1/99/0'
            )

            try:

                # Set driver var 'lines' to a list of lines
                self.__driver.run("window.lines = document.getElementById('searchResult').children[1].children")

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
            
            except RuntimeError:
                pass

class Magnet(api.qBitTorrent):
    """
    Handler for MAGNET URLs
    """

    __qualities = {
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
    ):
        from functools import partial
        from inspect import signature
            
        self.title = title.lower()
        self.leechers = leechers
        self.seeders = seeders
        self.url = url
        self.size = size

        self.quality = 0
        for term in self.__qualities:
            if term in self.title:
                self.quality = self.__qualities[term]

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

    def __repl__(self):
        from .text import abbreviate
        from .classOBJ import loc

        return f"<Magnet '{abbreviate(30, self.title)}' @{loc(self)}>"

class Soup:
    """
    Wrapper for bs4.BeautifulSoup

    Uses 'html.parser'
    """

    def __init__(self,
        soup: 'str | BeautifulSoup | bytes'
    ):
        from lxml.etree import _Element, HTML
        from bs4 import BeautifulSoup

        if isinstance(soup, BeautifulSoup):
            self.__soup = soup
        
        elif isinstance(soup, (str, bytes)):
            self.__soup = BeautifulSoup(
                soup,
                'html.parser'
            )

        self.select = self.__soup.select
        """Perform a CSS selection operation on the current element."""

        self.select_one = self.__soup.select_one
        """Perform a CSS selection operation on the current element."""

        self.__dom:_Element = HTML(str(soup))

    def element(self,
        by: Literal['class', 'id', 'xpath', 'name', 'attr'],
        name: str
    ) -> list[Self]:
        """
        Get List of Elements by query
        """

        by = by.lower()

        if by in ['class', 'classname', 'class_name']:
            items = self.__soup.select(f'.{name}')

        elif by in ['id']:
            items = self.__soup.find_all(id=name)

        elif by in ['xpath']:
            items = self.__dom.xpath(name)

        elif by in ['name']:
            items = self.__soup.find_all(name=name)

        elif by in ['attr', 'attribute']:
            t, c = name.split('=')
            items = self.__soup.find_all(attrs={t: c})

        return [Soup(i) for i in items]

class Driver:
    """
    Firefox Web Driver
    
    Wrapper for FireFox Selenium Session
    """
    from selenium.webdriver.remote.webelement import WebElement

    current_url: str
    """URL of the Current Page"""

    def __init__(
        self,
        headless: bool = True,
        cookies: (list[dict] | None) = None,
        extensions: list[str] = [],
        fast_load: bool = False,
        timeout: int = 300
    ):
        from selenium.webdriver import FirefoxService, FirefoxOptions, Firefox
        from selenium.common.exceptions import InvalidCookieDomainException
        from subprocess import CREATE_NO_WINDOW
        from threading import Thread
        from .process import SysTask
        from .terminal import Log
        from .file import temp
        
        Log.VERB(f'Starting Session: {headless=} | {fast_load=} | {timeout=}')

        service = FirefoxService()
        service.creation_flags = CREATE_NO_WINDOW # Suppress Console Output

        options = FirefoxOptions()
        options.add_argument("--disable-search-engine-choice-screen")

        if fast_load:
            options.page_load_strategy = 'eager'

        if headless:
            options.add_argument("--headless")

        # Start Chrome Session with options
        self._drvr = Firefox(options, service)

        self.Task = SysTask(self._drvr.service.process.pid)
        """Firefox.exe PID"""

        # Set Timeouts
        self._drvr.command_executor.set_timeout(timeout)
        self._drvr.set_page_load_timeout(timeout)
        self._drvr.set_script_timeout(timeout)

        # Iter through all given extension urls
        for url in extensions:

            Log.VERB(f'Installing Extension: {url}')
            
            # Temporary path for '.xpi' file
            xpifile = temp('firefox-extension', 'xpi')
            
            # Download the '.xpi' file
            download(
                url = url,
                path = xpifile
            )

            # Install the addon from the file
            self._drvr.install_addon(
                path = str(xpifile),
                temporary = True
            )

        # If any cookies are given
        if cookies:

            # Iter through cookies
            for cookie in cookies:
                try:
                    # Add cookie to the webdriver session
                    self._drvr.add_cookie(cookie)
                except InvalidCookieDomainException:
                    pass

        Thread(
            target = self.__background
        ).start()

    def reload(self):
        """Reload the Current Page"""
        from .terminal import Log

        Log.VERB(f'Reloading Page: {self.current_url=}')

        self._drvr.refresh()

    def clear_cookies(self):
        """Clear All Session Cookies"""
        from .terminal import Log

        Log.INFO('Clearing Session Cookies')

        self._drvr.delete_all_cookies()

    def run(self, code:str):
        """Run JavaScript Code on the Current Page"""
        from .terminal import Log
        from selenium.common.exceptions import JavascriptException

        Log.VERB(f'Executing JavaScript: {self.current_url=} |{code=}')

        try:

            response = self._drvr.execute_script(code)

            Log.VERB(f'JavaScript Executed: {response=}')

            return response
        
        except JavascriptException as e:

            # Truncate the Error Message
            mess: str = e.msg
            mess = mess[mess.find(':')+2:]
            mess = mess[:mess.find('\nStacktrace:')]

            raise RuntimeError(mess) from None

    def __background(self):
        from selenium.common.exceptions import WebDriverException
        from threading import main_thread
        from .terminal import Log
        from time import sleep

        while True:

            sleep(.25)

            try:
                # Update the current url value
                self.current_url = self._drvr.current_url
            
            # Stop if the session is closed
            except WebDriverException:
                return

            # Close session if the main thread is terminated
            if not main_thread().is_alive():

                Log.WARN('Closing Session: Main Thread Terminated')

                self._drvr.quit()

                return

    def element(self,
        by: Literal['class', 'id', 'xpath', 'name', 'attr'],
        name: str,
        wait: bool = True
    ) -> list[WebElement]:
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

        while True:

            elements = self._drvr.find_elements(BY, name)

            # If at least 1 element was found
            if (len(elements) > 0) or (not wait):

                Log.VERB(f"Found Elements: {elements=}")

                return elements

    def html(self):
        from selenium.common.exceptions import WebDriverException

        try:
            return self._drvr.page_source
        except WebDriverException:
            return None

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

        # Focus on the first tab
        self._drvr.switch_to.window(self._drvr.window_handles[0])

        # Open the url
        while True:
            try:
                self._drvr.get(url)
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

    def soup(self) -> 'Soup':
        """
        Get a soup of the current page
        """
        return Soup(
            self._drvr.page_source
        )

def download(
    url: str,
    path: 'Path',
    show_progress: bool = True,
    cookies = None
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
            stream = True,
            cookies = cookies
        )

        # Open the destination file
        file = path.open('wb')

        # Create a new progress bar
        pbar = tqdm(
            total = int(r.headers.get("content-length", 0)), # Total Download Size
            unit = "B",
            unit_scale = True
        )

        # Iter through all data in stream
        for data in r.iter_content(1024):

            # Update the progress bar
            pbar.update(len(data))

            # Write the data to the dest file
            file.write(data)

    else:

        # Download directly to the desination file
        urlretrieve(url, str(path))
