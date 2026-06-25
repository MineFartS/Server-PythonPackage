from qbittorrentapi import TorrentFile as __TorrentFile
from functools import cached_property
from .qbit import qBitTorrent as qbit
from dataclasses import dataclass
from typing import TYPE_CHECKING
from ...terminal import Log

if TYPE_CHECKING:
    from ...pc import Path
    from . import Torrent

@dataclass
class TorrentFile:
    
    torrent: Torrent
    raw: None | __TorrentFile

    def __repr__(self) -> str:
        from ...classtools import loc
        from ...text import abbr
        return f"<File '{abbr(30, self.name)}' @{loc(obj=self)}>"

    #===================================================

    def refresh(self) -> None:
        for f in self.torrent.files:
            if f.raw.id == self.raw.id:
                self.raw = f.raw
                return
        self.raw = None

    #===================================================

    @cached_property
    def path(self) -> Path:
        self.refresh()
        return self.torrent.path.child(self.raw.name)
    
    @cached_property
    def name(self) -> str:
        return self.path.name
    
    @cached_property
    def size(self) -> float:
        self.refresh()
        return self.raw.size

    @property
    def downloading(self) -> bool:
        self.refresh()
        return (self.raw.priority != 0) and (self.progress < 1)

    @property
    def finished(self) -> bool:
        self.refresh()
        return self.raw.progress == 1
    
    @property
    def enabled(self) -> bool:
        self.refresh()
        return self.raw.priority > 0

    #===================================================

    def _set_priority(self, priority:int) -> None:
        qbit.torrents_file_priority(
            torrent_hash = self.torrent.hash,
            file_ids = [self.raw.id],
            priority = priority
        )

    @Log.on_call
    def start(self) -> None:
        self._set_priority(1)

    @Log.on_call
    def stop(self) -> None:
        self._set_priority(0)

    #===================================================
