from qbittorrentapi import TorrentFile as __TorrentFile
from ...functools import copy_attrs
from typing import TYPE_CHECKING
from ...terminal import Log

if TYPE_CHECKING:
    from . import Torrent

class TorrentFile(__TorrentFile):

    def __init__(self,
        torrent: Torrent,
        tfile: __TorrentFile
    ) -> None:
        from functools import partial
        
        self.torrent = torrent
        
        self.file_priority = partial(torrent.file_priority, tfile.id)

        self.path = torrent.path.child(tfile.name)
        self.name = self.path.name

        copy_attrs(tfile, self)

    def __repr__(self) -> str:
        from ...classtools import loc
        from ...text import abbr
        return f"<File '{abbr(num=30, string=self.name)}' @{loc(obj=self)}>"

    id: str

    #===================================================

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
        self.file_priority(priority=1)

    @Log.on_call
    def stop(self) -> None:
        self.file_priority(priority=0)

    #===================================================
