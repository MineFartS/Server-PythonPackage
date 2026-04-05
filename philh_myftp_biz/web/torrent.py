from typing import Literal, TYPE_CHECKING, Any
from functools import cached_property

if TYPE_CHECKING:
    from qbittorrentapi import TorrentDictionary as __TorrentDict
    from qbittorrentapi import TorrentFile as __TorrentFile
    from ..array import SortFunc, FilterFunc, List
    from qbittorrentapi import Client
    from ..web import Driver
    from ..pc import Path

qualities: dict[str, int] = {
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
"""QUALITY LOOKUP TABLE"""

class TorrentFile:
    """Downloading Torrent File"""

    def __init__(self,
        torrent: '__TorrentDict',
        file: '__TorrentFile'
    ) -> None:
        from ..pc import Path
        
        self.path = Path(f'{torrent.save_path}/{file.name}')
        """Download Path"""
        
        self.size: float = file.size
        """File Size"""

        self.title: str = file.name[file.name.find('/')+1:]
        """File Name"""

        self._id: str = file.id
        """File ID"""

        self._torrent = torrent
        """Torrent"""

    @property
    def _file(self) -> 'None|__TorrentFile':
        from qbittorrentapi.exceptions import TorrentFileNotFoundError

        try:
            return self._torrent.files[self._id]
        
        except TorrentFileNotFoundError:
            pass

    @property
    def progress(self) -> None | float:
        from qbittorrentapi.exceptions import NotFound404Error
        
        try:
            if self._file:
                return self._file.progress
        
        except NotFound404Error:
            pass

    def start(self,
        force: bool = False
    ) -> None:
        """
        Start downloading the file
        """
        from ..terminal import Log

        Log.VERB(f'Downloading File: {force=} | {self}]')

        self._torrent.file_priority(
            file_ids = self._id,
            priority = (7 if force else 1)
        )

    @property
    def enabled(self) -> bool:

        if self._file:

            priority: int = self._file.priority

            return (priority > 0)
        
        else:
            return False

    @property
    def downloading(self) -> bool:

        return (self.enabled and (not self.finished))

    def stop(self) -> None:
        """
        Stop downloading the file

        Ignores error if the magnet is not found
        """
        from qbittorrentapi.exceptions import NotFound404Error
        from ..terminal import Log

        Log.VERB(f'Stopping File: {self}')

        try:
            self._torrent.file_priority(
                file_ids = self._id,
                priority = 0
            )
        except NotFound404Error:
            pass

    @property
    def finished(self) -> bool:
        """
        Check if the file is finished downloading
        """
        return (self.progress == 1)

    def __repr__(self) -> str:
        from ..classtools import loc
        from ..text import abbr

        return f"<File '{abbr(num=30, string=self.title)}' @{loc(obj=self)}>"

class Torrent:

    def __init__(self,
        qbit: qBitTorrent,
        hash: str
    ):
        
        self.qbit = qbit
        self.timeout = qbit.timeout

        self.hash = hash

    #===================================================

    def __qbit_getter(name:str, defv:Any):
        return property(lambda s: getattr(s.qbit, name, defv))

    _client: 'Client' = __qbit_getter('_client', None)

    priority: int = __qbit_getter('priority', None)

    seeders: int = __qbit_getter('num_complete', -1)

    leechers: int = __qbit_getter('num_incomplete', -1)

    title: str = __qbit_getter('name', None)

    #===================================================

    def start(self):
        if self._tdict:
            self._tdict.start()

    @property
    def _tdict(self) -> '__TorrentDict | None':
        
        for t in self._client.torrents_info():
        
            if t.hash == self.hash:

                return t

    @property
    def files(self) -> list[TorrentFile]:
        """
        List of all files in Magnet Download

        Waits for at least one file to be found before returning
        """
        from ..time import Timeout
        from ..terminal import Log

        Log.VERB(f'Scanning Files: {self}')

        timeout = Timeout(self.timeout)

        # Wait for torrent creation
        while self._tdict is None:
            timeout.check()
            
        self._tdict.setForceStart(True)

        # Wait for files to populate
        while len(self._tdict.files) == 0:
            timeout.check()

        self._tdict.setForceStart(False)

        return [TorrentFile(self._tdict,f) for f in self._tdict.files]

    @property
    def selected_files(self):
        return [f for f in self.files if f.enabled]

    def stop(self,
        rm_files: bool = True
    ) -> None:
        """Stop downloading a Magnet"""
        from ..terminal import Log

        Log.VERB(f'Stopping: {rm_files=} | {self}')

        self._tdict.delete(delete_files=rm_files)

    @property
    def finished(self) -> None | bool:
        """Check if a magnet is finished downloading"""
        
        if self._tdict:

            state = self._tdict.state_enum
            
            return (state.is_uploading or state.is_complete)

    @property
    def errored(self) -> bool:
        """Check if a magnet is errored"""

        if self._tdict:
            return self._tdict.state_enum.is_errored
        else:
            return False
        
    @property
    def downloading(self) -> None | bool:
        """Check if a magnet is downloading"""
        
        if self._tdict:
            return self._tdict.state_enum.is_downloading

    @property
    def exists(self) -> bool:
        """Check if a magnet is in the download queue"""
        
        return (self._tdict != None)

    @property
    def stalled(self) -> bool:
        """Check if a magnet is stalled"""
        
        if self._tdict:
            return (self._tdict.state_enum.value == 'stalledDL')
        else:
            return False

    def reannounce(self) -> None:
        from ..terminal import Log

        Log.VERB(f'Reannouncing: {self}')

        if self._tdict:

            self._tdict.reannounce()

    def recheck(self) -> None:
        from ..terminal import Log

        Log.VERB(f'Rechecking: {self}')

        if self._tdict:

            self._tdict.recheck()

class qBitTorrent:
    """Client for qBitTorrent Web Server"""

    def __init__(self,
        host: str,
        username: str,
        password: str,
        port: int = 8080,
        timeout: int = 3600 # 1 hour
    ) -> None:
        from ..terminal import Log

        Log.VERB(
            f'Connecting to qBitTorrentAPI\n'+ \
            f'{host=} | {port=}\n'+ \
            f'{username=}\n'+ \
            f'{timeout=}'
        )

        self.host: str = host
        self.port: int = port
        self.timeout: int = timeout

        self.__login = (username, password)

    @cached_property
    def _rclient(self) -> 'Client':
        from qbittorrentapi import Client

        return Client(
            host = self.host,
            port = self.port,
            username = self.__login[0],
            password = self.__login[1],
            VERIFY_WEBUI_CERTIFICATE = False,
            REQUESTS_ARGS = {'timeout': (self.timeout, self.timeout)}
        )

    @property
    def _client(self) -> 'Client':
        """Wait for server connection, then returns qbittorrentapi.Client"""
        from qbittorrentapi.exceptions import LoginFailed, Forbidden403Error, APIConnectionError
        from ..time import Timeout
        from ..terminal import Log

        timeout = Timeout(self.timeout)

        while True:

            try:

                self._rclient.torrents_info()

                return self._rclient
            
            except LoginFailed, Forbidden403Error, APIConnectionError:
                Log.VERB('qBitTorrentAPI Connection Error')

            timeout.check()

    @property
    def connected(self) -> bool:
        """Check if qBitTorrent is connected to the internet"""

        tinfo = self._client.transfer.info()

        conn_status = tinfo.connection_status

        return (conn_status == 'connected')

    def clear(self,
        rm_files: bool = True,
        func: FilterFunc['Torrent'] = lambda t: True
    ) -> None:
        """Remove all Magnets from the download queue"""
        from ..text import from_function
        from ..terminal import Log

        Log.VERB(
            f'Clearing Download Queue:\n'+ \
            f'{rm_files=}\n'+ \
            'func='+from_function(func)
        )

        for t in self._client.torrents_info():

            torrent = Torrent(self, t.hash)

            if func(torrent):
            
                Log.VERB(f'Deleting Queue Item: {rm_files=} | {torrent.title=}')
                
                torrent.stop(rm_files)

    def sort(self,
        func: SortFunc['Torrent']
    ) -> None:
        """Sort the download queue"""
        from ..text import from_function
        from ..terminal import Log
        from ..array import List

        Log.VERB(
            f'Sorting Download Queue:\n'+ \
            'func='+from_function(func)
        )

        torrents = List(Torrent(self, t.hash) for t in self._client.torrents_info())

        torrents.sort(func).reverse()

        # Iterate through reversed list of torrents
        for t in torrents:
            # Move to top of queue
            t._tdict.top_priority()

    @property
    def queue(self) -> list[Torrent]:
        return [Torrent(self, t.hash) for t in self._client.torrents_info()]

    def randomize_port(self) -> None:
        from random import randint
        
        # Update preference
        self._client.app_setPreferences(preferences={
            'listen_port': randint(a=10000, b=60000)
        })

class Magnet(Torrent):
    """Handler for MAGNET URLs"""

    def __init__(self,
        qbit: qBitTorrent,
        title: str = '',
        seeders: int = -1,
        leechers: int = -1,
        url: str = '',
        size: str = -1
    ) -> None:
        from urllib.parse import urlparse, parse_qs

        #===================================================

        # Get the value of the 'xt' parameter (it's a list, so take the first element)
        XT: str = parse_qs(urlparse(url).query)['xt'][0]

        # The hash follows 'urn:btih:' or 'urn:btmh:'
        if XT.startswith('urn:btih:'):
            _hash = XT[len('urn:btih:'):].lower()
        
        elif XT.startswith('urn:btmh:'): # for v2 magnets
            _hash = XT[len('urn:btmh:'):].lower()

        super().__init__(qbit, _hash) # pyright: ignore[reportPossiblyUnboundVariable]
            
        #===================================================

        self._title: str = title.lower().strip('\n')
        self._leechers: int = leechers
        self._seeders: int = seeders
        self.size: str = size
        self.url: str = url

        #===================================================

        self.quality = 0
        for term, quality in qualities.items():
            
            if term in self.title:
                
                self.quality: int = quality

        #===================================================

    #===================================================
    
    def __torrent_getter(name:str):
        return property(lambda s: getattr(
            s.qbit, name,
            getattr(s, '_'+name)
        ))

    title: str = __torrent_getter('title')

    seeders: int = __torrent_getter('seeders')

    leechers: int = __torrent_getter('leechers')

    #===================================================

    def start(self,
        path: 'None|str|Path' = None
    ) -> None:
        """Start Downloading a Magnet"""
        from ..terminal import Log

        Log.VERB(
            f'Starting\n'+ \
            f'{self=}\n'+ \
            f'{path=}'
        )

        if path:
            path = str(path)

        if self._tdict:
            self._tdict.start()
        
        else:
            self._client.torrents_add(
                urls = self.url,
                save_path = path
            )

    def restart(self) -> None:
        """Restart Downloading a Magnet"""
        from ..terminal import Log

        Log.VERB(f'Restarting: {self}')

        self.stop()
        self.start()

    def __repr__(self) -> str:
        from ..classtools import loc
        from ..text import abbr

        return f"<Magnet '{abbr(30, self.title.strip())}' @{loc(self)}>"

class thePirateBay:
    """
    thePirateBay

    'https://thepiratebay.org/'
    """

    urls: list[str] = [
        "thepiratebay11.com",
        "thepiratebay10.info",
        "thepiratebay7.com",
        "thepiratebay0.org",
        "thehiddenbay.com",
        "piratebay.live",
        "tpb.party"
    ]
    
    def __init__(self,
        url: Literal[*urls] = "thepiratebay11.com", # pyright: ignore[reportInvalidTypeForm]
        driver: 'Driver' = None,
        qbit: qBitTorrent = None
    ) -> None:
        from ..functools import TransitoryCache
        from ..web import URL
        
        self.url = URL(f'https://{url}/search/')
        """tpb mirror url"""

        self._qbit: qBitTorrent = qbit
        """qBitTorrent Session"""
        
        if driver:
            self._driver: Driver = driver
        else:
            self._driver = Driver()

        self._cache: 'TransitoryCache[List[Magnet]]' = TransitoryCache(expire=36000) # 10 hours

    def search(self, *queries:str) -> List[Magnet]:
        """Search thePirateBay for magnets"""
        from ..array import List
        from .. import VERBOSE

        VERBOSE.pause()
        
        magnets = []

        _queries = []

        for q in queries:
            _queries += [
                q,
                q.replace('.', '').replace("'", ''),
                q.replace('.', ' ').replace("'", ' ')
            ]

        for q in _queries:
            magnets += self.rsearch(q)

        VERBOSE.resume()

        return List(magnets)

    def rsearch(self, query:str) -> list[Magnet]:
        """Search thePirateBay for magnets"""
        from ..terminal import Log
        from ..db import Size

        # Open the search in a url
        self._driver.open(
            url = self.url.child(query)
        )

        # Set driver var 'lines' to a list of lines
        try:
            self._driver.run("window.lines = document.getElementById('searchResult').children[1].children")
        except RuntimeError:
            self._cache[query] = []
            return []
        
        magnets: list[Magnet] = []

        # Iter from 0 to # of lines
        for x in range(0, self._driver.run('return lines.length')):

            _run = lambda c: self._driver.run(f'return lines[{x}]{c}')

            try:

                # Yield a magnet instance
                magnets += [Magnet(

                    title = _run(".children[1].textContent"),

                    seeders = int(_run(".children[5].textContent")),

                    leechers = int(_run(".children[6].textContent")),

                    url = _run(".children[3].children[0].children[0].href"),
                    
                    size = Size.to_bytes(_run(".children[4].textContent")),

                    qbit = self._qbit

                )]

            except KeyError, RuntimeError:
                Log.VERB('', exc_info=True)

        self._cache[query] = magnets

        return magnets
