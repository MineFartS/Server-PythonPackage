from ...functools import singleton
from typing import TYPE_CHECKING
from ...terminal import Log

from qbittorrentapi import TorrentDictionary as __TorrentDict
from qbittorrentapi import TorrentState as __TorrentState
from qbittorrentapi import TorrentFile as __TorrentFile
from qbittorrentapi import Client as __Client

from ...array import SortFunc, FilterFunc, List

from qbittorrentapi.log import LogAPIMixIn
from qbittorrentapi.rss import RSSAPIMixIn
from qbittorrentapi.search import SearchAPIMixIn
from qbittorrentapi.sync import SyncAPIMixIn
from qbittorrentapi.torrentcreator import TorrentCreatorAPIMixIn
from qbittorrentapi.torrents import TorrentsAPIMixIn
from qbittorrentapi.transfer import TransferAPIMixIn

if TYPE_CHECKING:
    from .magnet import Torrent

@singleton
class qBitTorrent(
    LogAPIMixIn,
    SyncAPIMixIn,
    TransferAPIMixIn,
    TorrentsAPIMixIn,
    TorrentCreatorAPIMixIn,
    RSSAPIMixIn,
    SearchAPIMixIn
):

    def connect(self,
        host: str,
        username: str,
        password: str,
        port: int = 8080,
        timeout: int = 3600 # 1 hour
    ) -> None:
        from qbittorrentapi.exceptions import LoginFailed, Forbidden403Error, APIConnectionError
        from ...time import Timeout
        from random import randint

        super().__init__(
            host, port, username, password,
            VERIFY_WEBUI_CERTIFICATE = False,
            REQUESTS_ARGS = {'timeout': (timeout, timeout)}
        )

        self._timeout = lambda: Timeout(timeout)
        
        to = self._timeout()

        while True:
            try:
                to.check()
                self.torrents_info()
                break
            except LoginFailed, Forbidden403Error, APIConnectionError:
                Log.VERB(exc_info=True)

        self.app_setPreferences({
            'listen_port': randint(a=10000, b=60000)
        })

    @Log.on_call
    def clear(self,
        rm_files: bool = True,
        func: FilterFunc[Torrent] = lambda t: True
    ) -> None:
        
        torrents = self.queue
        torrents.filter(func)

        for torrent in torrents:
            torrent.stop(rm_files)

    @Log.on_call
    def sort(self,
        func: SortFunc[Torrent]
    ) -> None:
        torrents = self.queue
        torrents.sort(func)
        torrents.reverse()

        (t.top_priority() for t in torrents)

    @property
    def queue(self) -> List[Torrent]:

        items = List()

        for t in self.torrents_info():
            t.__class__ = Torrent
            items += t

        return items
    
