from typing import TYPE_CHECKING, ClassVar, Callable, Literal
from ..functools import TransitoryCache, singleton
from functools import cached_property
from dataclasses import dataclass
from ..json import LookupTable
from ..web import URL

if TYPE_CHECKING:
    from qbittorrentapi import TorrentDictionary as __TorrentDict
    from qbittorrentapi import TorrentState as __TorrentState
    from qbittorrentapi import TorrentFile as __TorrentFile
    from ..array import SortFunc, FilterFunc, List
    from qbittorrentapi import Client as __Client
    from .driver import Driver
    from ..pc import Path

qualities: list[str] = {
    'hdtv', 'tvrip', '2160p', 
    '1440p', '1080p', '720p',
    '480p', '360p', '4K'
}

#======================================================================

class TorrentFile:

    def __init__(self,
        torrent: Torrent,
        file: __TorrentFile
    ) -> None:
        
        self.torrent = torrent
        
        self.size: float = file.size
        self.id: str = file.id

        self.path = torrent.save_path.child(file.name)
        self.name = self.path.name

    def __repr__(self) -> str:
        from ..classtools import loc
        from ..text import abbr
        return f"<File '{abbr(num=30, string=self.name)}' @{loc(obj=self)}>"

    #===================================================

    @property
    def _file(self) -> None | __TorrentFile:
        if (tdict := self.torrent._tdict):
            return tdict.files[self.id]
        
    #===================================================

    @property
    def downloading(self) -> None | bool:
        if (file := self._file):
            return (file.priority != 0) and (file.progress < 1)

    @property
    def finished(self) -> None | bool:
        if (file := self._file):
            return file.progress == 1
    
    @property
    def enabled(self) -> None | bool:
        if (file := self._file):
            return file.priority > 0

    #===================================================

    def _set_priority(self, p:int) -> None:
        self.torrent.qbit._client.torrents_filePrio(
            torrent_hash = self.torrent.hash, 
            file_ids = [self.id],
            priority = p
        )

    def start(self) -> None:
        self._set_priority(1)

    def stop(self) -> None:
        self._set_priority(0)

    #===================================================

#======================================================================

@dataclass
class Torrent:

    qbit: qBitTorrent
    hash: str

    def __repr__(self) -> str:
        from ..classtools import loc
        from ..text import abbr

        return f"<Torrent '{abbr(num=30, string=self.name)}' @{loc(obj=self)}>"

    #===================================================

    def __getattr__(self, name:str):

        match name:
            
            case 'priority' | 'seeders' | 'leechers':
                return getattr(self._tdict, name, -1)
            
            case 'name':
                return getattr(self._tdict, name, "")
            
            case 'state_enum':
                return getattr(self._tdict, name, None)
            
            case 'errored' | 'downloading':
                return getattr(self.state_enum, f'is_{name}', None)
            
            case 'start' | 'reannounce' | 'recheck' | 'top_priority':
                return getattr(self._tdict, name, lambda:...)
            
            case 'force':
                return getattr(self._tdict, 'setForceStart', lambda _:...)
            
            case _:
                return super().__getattribute__(name) # Raises Error

    priority: ClassVar[int]
    seeders: ClassVar[int]
    leechers: ClassVar[int]
    
    name: ClassVar[str]
    
    state_enum: ClassVar[__TorrentState]
    
    errored: ClassVar[None|bool]
    downloading: ClassVar[None|bool]

    start: ClassVar[Callable[[], None]]
    reannounce: ClassVar[Callable[[], None]]
    recheck: ClassVar[Callable[[], None]]
    top_priority: ClassVar[Callable[[], None]]

    force: ClassVar[Callable[[bool], None]]

    #===================================================

    @property
    def _tdict(self) -> None | __TorrentDict:
        return next(
            (t for t in self.qbit._client.torrents_info() if t.hash==self.hash), 
            None
        )
            
    def wait(self) -> None:
        from ..time import Timeout

        timeout = Timeout(self.qbit.timeout)

        while self._tdict is None:
            timeout.check()

        self.force(True)

        while len(self._tdict.files) == 0:
            timeout.check()

        self.force(False)

    @property
    def files(self) -> List[TorrentFile]:
        from ..json import List

        if (tdict := self._tdict):
            return List(TorrentFile(self, f) for f in tdict.files)
        else:
            return List()

    @property
    def enabled_files(self) -> List[TorrentFile]:
        return self.files.filtered(lambda f: f.enabled)

    def stop(self, rm_files:bool=True) -> None:
        if (tdict := self._tdict):
            tdict.delete(rm_files)

    @property
    def finished(self) -> None | bool:
        if (state := self.state_enum):
            return (state.is_uploading or state.is_complete)

    @property
    def exists(self) -> bool:
        return (self._tdict != None)

    @property
    def stalled(self) -> None | bool:
        if (state := self.state_enum):
            return (state.value == 'stalledDL')

    @cached_property
    def save_path(self) -> None | Path:
        from ..pc import Path

        if (tdict := self._tdict):
            return Path(tdict.save_path)

#======================================================================

@dataclass
class qBitTorrent:

    host: str
    username: str
    password: str
    port: int = 8080
    timeout: int = 3600 # 1 hour

    @property
    def _client(self) -> __Client:
        from qbittorrentapi.exceptions import LoginFailed, Forbidden403Error, APIConnectionError
        from qbittorrentapi import Client
        from ..time import Timeout
        from ..terminal import Log
        from random import randint

        timeout = Timeout(self.timeout)

        if not hasattr(self, '_rclient'):

            self._rclient = Client(
                host = self.host,
                port = self.port,
                username = self.username,
                password = self.password,
                VERIFY_WEBUI_CERTIFICATE = False,
                REQUESTS_ARGS = {'timeout': (self.timeout, self.timeout)}
            )

            self._rclient.app_setPreferences({
                'listen_port': randint(a=10000, b=60000)
            })

        while True:
            try:
                self._rclient.torrents_info()
                return self._rclient
            except LoginFailed, Forbidden403Error, APIConnectionError:
                Log.VERB(exc_info=True)

            timeout.check()

    @property
    def connected(self) -> bool:
        """Check if qBitTorrent is connected to the internet"""
        return (self._client.transfer.info().connection_status == 'connected')

    def clear(self,
        rm_files: bool = True,
        func: FilterFunc['Torrent'] = lambda t: True
    ) -> None:
        from ..text import from_function
        from ..terminal import Log

        Log.VERB(
            f'Clearing Download Queue:\n'+ \
            f'{rm_files=}\n'+ \
            'func='+from_function(func)
        )

        for torrent in self.queue:
            if func(torrent):
                Log.VERB(f'Deleting Queue Item: {rm_files=} | {torrent.name=}')                
                torrent.stop(rm_files)

    def sort(self,
        func: SortFunc['Torrent']
    ) -> None:
        from ..text import from_function
        from ..terminal import Log

        Log.VERB(
            f'Sorting Download Queue:\n'+ \
            'func='+from_function(func)
        )

        torrents = self.queue
        torrents.sort(func)
        torrents.reverse()

        (t.top_priority() for t in torrents)

    @property
    def queue(self) -> List[Torrent]:
        from ..array import List
        return List(Torrent(self, t.hash) for t in self._client.torrents_info())

#======================================================================

class NameParser:
        
    def __init__(self, name:str) -> None:
        from PTN import parse

        self._get = parse(name).get
        
        self.name = name

        self.title: str|None = self._get('title')

        self.season: int|list[int]|None = self._get('season')

        self.episode: int|list[int]|None = self._get('episode')

    @cached_property
    def year(self) -> list[int] | int | None:
        from re import findall

        if self._get('year'):
            return self._get('year')

        m = findall(
            pattern = "(?:19[0-9]|20[0-2])[0-9]",
            string = self.name
        )
        
        if len(m) > 1:

            years = list(range(int(m[0]), int(m[-1]) + 1))
            
            if len(years) > 0:
                return years
        
        elif m:
            return int(m[0])

    @cached_property
    def quality(self) -> None | str:
        for quality in qualities:
            if quality in self.name:
                return quality

#======================================================================

class Magnet(Torrent, NameParser):

    def __init__(self,
        qbit: qBitTorrent,
        name: str = '',
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

        Torrent.__init__(self, qbit, _hash) # pyright: ignore[reportPossiblyUnboundVariable]

        #===================================================
        
        self.leechers = leechers
        self.seeders = seeders
        self.size  = size
        self.url = url

        NameParser.__init__(self, name.lower().strip('\n'))

        #===================================================

    #===================================================

    def start(self,
        path: 'None|str|Path' = None
    ) -> None:
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
            self.qbit._client.torrents_add(
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

        return f"<Magnet '{abbr(30, self.name)}' @{loc(self)}>"

    #===================================================

#======================================================================

@singleton
class thePirateBay:
    """
    thePirateBay

    'https://thepiratebay.org/'
    """

    url = URL("https://thepiratebay11.com/search/")
    driver: 'Driver' = None
    qbit: qBitTorrent = None

    cache: 'TransitoryCache[List[Magnet]]' = TransitoryCache('torrent', expire=36000) # 10 hours

    def search(self, *queries:str) -> List[Magnet]:
        """Search thePirateBay for magnets"""
        from ..array import List
        from .. import VERBOSE

        magnets = List()

        VERBOSE.pause()

        for q in queries:
            magnets += self.rsearch(q)
            magnets += self.rsearch(q.replace('.', '').replace("'", ''))
            magnets += self.rsearch(q.replace('.', ' ').replace("'", ' '))

        VERBOSE.resume()

        magnets.flatten()
        magnets.uniquify()

        return magnets

    def rsearch(self, query:str) -> list[Magnet]:
        """Search thePirateBay for magnets"""
        from ..terminal import Log
        from ..db import Size

        if self.driver is None:
            self.driver = Driver()

        # Open the search in a url
        self.driver.open(
            url = self.url.child(query)
        )

        # Set driver var 'lines' to a list of lines
        try:
            self.driver.run("window.lines = document.getElementById('searchResult').children[1].children")
        except RuntimeError:
            self.cache[query] = []
            return []
        
        magnets: list[Magnet] = []

        # Iter from 0 to # of lines
        for x in range(0, self.driver.run('return lines.length')):

            _run = lambda c: self.driver.run(f'return lines[{x}]{c}')

            try:

                # Yield a magnet instance
                magnets += [Magnet(

                    name = _run(".children[1].textContent"),

                    seeders = int(_run(".children[5].textContent")),

                    leechers = int(_run(".children[6].textContent")),

                    url = _run(".children[3].children[0].children[0].href"),
                    
                    size = Size.to_bytes(_run(".children[4].textContent")),

                    qbit = self.qbit

                )]

            except KeyError, RuntimeError:
                Log.VERB('', exc_info=True)

        self.cache[query] = magnets

        return magnets

#======================================================================
