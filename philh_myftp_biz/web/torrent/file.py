from qbittorrentapi import TorrentFile as __TorrentFile
from functools import cached_property
from .qbit import qBitTorrent as qbit
from typing import TYPE_CHECKING
from ...terminal import Log

if TYPE_CHECKING:
    from . import Torrent

class TorrentFile(__TorrentFile):
        
    id: str
    torrent: Torrent

    def __repr__(self) -> str:
        from ...classtools import loc
        from ...text import abbr

        name = getattr(self, 'name', None)

        return f"<File '{abbr(30, name)}' @{loc(obj=self)}>"

    #===================================================

    @cached_property
    def path(self):
        return self.torrent.path.child(self.name)
    
    @cached_property
    def name(self):
        return self.path.name

    @property
    def downloading(self) -> None | bool:
        return (self.priority != 0) and (self.progress < 1)

    @property
    def finished(self) -> None | bool:
        return self.progress == 1
    
    @property
    def enabled(self) -> None | bool:
        return self.priority > 0

    #===================================================

    def _set_priority(self, priority:int):
        qbit.torrents_file_priority(
            torrent_hash = self.torrent.hash,
            file_ids = [self.id],
            priority = priority
        )

    @Log.on_call
    def start(self) -> None:
        self._set_priority(1)

    @Log.on_call
    def stop(self) -> None:
        self._set_priority(0)

    #===================================================
