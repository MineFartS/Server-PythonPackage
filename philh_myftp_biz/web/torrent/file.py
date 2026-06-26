from qbittorrentapi import TorrentFile as __TorrentFile
from ...functools import cached_property
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
    id: str

    def __repr__(self) -> str:
        from ...classtools import loc
        from ...text import abbr
        return f"<File '{abbr(30, self.name)}' @{loc(obj=self)}>"

    #===================================================

    @property
    def raw(self) -> None | __TorrentFile:
        for file in self.torrent.raw.files:
            if file.id == self.id:
                return file

    #===================================================

    @cached_property
    def path(self) -> Path:
        return self.torrent.path.child(self.raw.name)
    
    @cached_property
    def name(self) -> str:
        from os.path import basename
        return basename(self.raw.name)
    
    @cached_property
    def size(self) -> float:
        return self.raw.size

    @property
    def downloading(self) -> bool:
        return (self.raw.priority != 0) and (self.raw.progress < 1)

    @property
    def finished(self) -> bool:
        return self.raw.progress == 1
    
    @property
    def enabled(self) -> bool:
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
