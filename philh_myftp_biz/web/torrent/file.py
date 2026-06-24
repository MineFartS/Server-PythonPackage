from qbittorrentapi import TorrentFile as __TorrentFile
from functools import cached_property
from typing import TYPE_CHECKING
from ...terminal import Log

if TYPE_CHECKING:
    from . import Torrent

class TorrentFile(__TorrentFile):

    def __init__(self) -> None:
        pass
        
    id: str
    torrent: Torrent

    def __repr__(self) -> str:
        from ...classtools import loc
        from ...text import abbr
        return f"<File '{abbr(num=30, string=self.name)}' @{loc(obj=self)}>"

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

    @Log.on_call
    def start(self) -> None:
        self.torrent.file_priority(self.id, 1)

    @Log.on_call
    def stop(self) -> None:
        self.torrent.file_priority(self.id, 0)

    #===================================================
