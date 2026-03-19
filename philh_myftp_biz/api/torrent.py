from typing import Literal, TYPE_CHECKING
from functools import cached_property

if TYPE_CHECKING:
    from qbittorrentapi import Client, TorrentDictionary
    from qbittorrentapi import TorrentFile as __TorrentFile
    from ..array import SortFunc, FilterFunc
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
    """
    Downloading Torrent File
    """

    def __init__(self,
        torrent: 'TorrentDictionary',
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
        func: FilterFunc['TorrentDictionary'] = lambda t: True
    ) -> None:
        """Remove all Magnets from the download queue"""
        from ..text import from_function
        from ..terminal import Log

        Log.VERB(
            f'Clearing Download Queue:\n'+ \
            f'{rm_files=}\n'+ \
            'func='+from_function(func)
        )

        for torrent in self._client.torrents_info():

            if func(torrent):
            
                Log.VERB(f'Deleting Queue Item: {rm_files=} | {torrent.name=}')
                
                torrent.delete(rm_files)

    def sort(self,
        func: SortFunc['TorrentDictionary']
    ) -> None:
        """Sort the download queue"""
        from ..text import from_function
        from ..terminal import Log

        Log.VERB(
            f'Sorting Download Queue:\n'+ \
            'func='+from_function(func)
        )

        torrents = sorted(
            self._client.torrents_info(),
            key = func
        )

        # Iterate through reversed list of torrents
        for t in reversed(torrents):

            # Move to top of queue
            t.top_priority()

    def randomize_port(self) -> None:
        from random import randint
        
        # Update preference
        self._client.app_setPreferences(preferences={
            'listen_port': randint(a=10000, b=60000)
        })

class Magnet(qBitTorrent):
    """Handler for MAGNET URLs"""

    def __init__(self,
        title: str = '',
        seeders: int = -1,
        leechers: int = -1,
        url: str = '',
        size: str = -1,
        qbit: 'qBitTorrent' = None
    ) -> None:
        from urllib.parse import urlparse, parse_qs

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
        for term, quality in qualities.items():
            
            if term in self.title:
                
                self.quality: int = quality

        if qbit:
            for name in ['_rclient', 'timeout']:
                setattr(
                    self, name,
                    getattr(qbit, name)
                )

    @property
    def _torrent(self) -> None | TorrentDictionary:

        for t in self._client.torrents_info():
            
            #
            if t.hash == self.hash:

                return t

    def start(self,
        path: 'str|Path' = None
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

        if self._torrent:
            self._torrent.start()
        
        else:
            self._client.torrents_add(
                urls = self.url,
                save_path = path
            )

    def reannounce(self) -> None:
        from ..terminal import Log

        Log.VERB(f'Reannouncing: {self}')

        if self._torrent:

            self._torrent.reannounce()

    def recheck(self) -> None:
        from ..terminal import Log

        Log.VERB(f'Rechecking: {self}')

        if self._torrent:

            self._torrent.recheck()

    def restart(self) -> None:
        """Restart Downloading a Magnet"""
        from ..terminal import Log

        Log.VERB(f'Restarting: {self}')

        self.stop()
        self.start()

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
        while self._torrent is None:
            timeout.check()
            
        self._torrent.setForceStart(True)

        # Wait for files to populate
        while len(self._torrent.files) == 0:
            timeout.check()

        self._torrent.setForceStart(False)

        return [TorrentFile(self._torrent,f) for f in self._torrent.files]

    def stop(self,
        rm_files: bool = True
    ) -> None:
        """Stop downloading a Magnet"""
        from ..terminal import Log

        Log.VERB(f'Stopping: {rm_files=} | {self}')

        self._torrent.delete(delete_files=rm_files)

    @property
    def finished(self) -> None | bool:
        """Check if a magnet is finished downloading"""
        
        if self._torrent:

            state = self._torrent.state_enum
            
            return (state.is_uploading or state.is_complete)

    @property
    def errored(self) -> bool:
        """Check if a magnet is errored"""

        if self._torrent:
            return self._torrent.state_enum.is_errored
        else:
            return False
        
    @property
    def downloading(self) -> None | bool:
        """Check if a magnet is downloading"""
        
        if self._torrent:
            return self._torrent.state_enum.is_downloading

    @property
    def exists(self) -> bool:
        """Check if a magnet is in the download queue"""
        
        return (self._torrent != None)

    @property
    def stalled(self) -> bool:
        """Check if a magnet is stalled"""
        
        if self._torrent:
            return (self._torrent.state_enum.value == 'stalledDL')
        else:
            return False

    def __repr__(self) -> str:
        from ..classtools import loc
        from ..text import abbr

        return f"<Magnet '{abbr(30, self.title.strip())}' @{loc(self)}>"

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
        driver: 'Driver' = None,
        qbit: qBitTorrent = None
    ) -> None:
        from ..functools import TransitoryCache
        
        self.tpburl: str = (f'https://{url}' + '/search/{}/1/99/0')
        """tpb mirror url"""

        self._qbit: qBitTorrent = qbit
        """qBitTorrent Session"""
        
        if driver:
            self._driver: Driver = driver
        else:
            self._driver = Driver()

        self._cache: TransitoryCache[list[Magnet]] = TransitoryCache(expire=36000) # 10 hours

    def search(self,
        query: str
    ) -> list[Magnet]:
        """
        Search thePirateBay for magnets

        EXAMPLE:
        for magnet in thePirateBay.search('term'):
            magnet
        """
        from ..db import Size

        if self._cache[query]:
            return self._cache[query] # pyright: ignore[reportReturnType]

        # Remove all "." & "'" from query
        query = query.replace('.', '').replace("'", '')

        # Open the search in a url
        self._driver.open(
            url = self.tpburl.format(query)
        )

        _run = self._driver.run

        # Set driver var 'lines' to a list of lines
        try:
            _run("window.lines = document.getElementById('searchResult').children[1].children")
        except RuntimeError:
            self._cache[query] = []
            return []
        
        magnets: list[Magnet] = []

        # Iter from 0 to # of lines
        for x in range(0, _run('return lines.length')):

            try:

                # Yield a magnet instance
                magnets += [Magnet(

                    title = _run(f"return lines[{x}].children[1].textContent"),

                    seeders = int(_run(f"return lines[{x}].children[5].textContent")),

                    leechers = int(_run(f"return lines[{x}].children[6].textContent")),

                    url = _run(f"return lines[{x}].children[3].children[0].children[0].href"),
                    
                    size = Size.to_bytes(_run(f"return lines[{x}].children[4].textContent")),

                    qbit = self._qbit

                )]

            except KeyError, RuntimeError:
                pass

        self._cache[query] = magnets

        return magnets