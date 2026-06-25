from qbittorrentapi import TorrentDictionary
from functools import cached_property
from .qbit import qBitTorrent as qbit
from dataclasses import dataclass
from .file import TorrentFile
from ...terminal import Log
from typing import ClassVar
from ...json import List

@dataclass
class Torrent:

    raw: None | TorrentDictionary

    def __repr__(self) -> str:
        from ...classtools import loc
        from ...text import abbr

        return f"<Torrent '{abbr(30, self.name)}' @{loc(self)}>"
    
    __str__ = __repr__

    def __format__(self, spec) -> str:
        return str(self).__format__(spec)
    
    #===================================================

    def refresh(self):
        for torr in qbit.queue:
            if torr.hash == self.hash:
                self.raw = torr.raw
                return
        self.raw = None

    #===================================================

    @cached_property
    def path(self):
        from ...pc import Path
        self.refresh()
        return Path(self.raw.save_path)

    @property
    def finished(self) -> None | bool:
        self.refresh()
        state = self.raw.state_enum
        return (state.is_uploading or state.is_complete)

    @property
    def stalled(self) -> None | bool:
        self.refresh()
        return (self.raw.state_enum.value == 'stalledDL')

    #===================================================

    @cached_property
    def files(self) -> List[TorrentFile]:
        self.refresh()

        to = qbit._timeout()

        self.raw.setForceStart(True)

        try:
            
            while len(self.raw.files) == 0:
                to.check()

            files = []

            for f in self.raw.files:
                files += [TorrentFile(self, f)]

            return List(files)
        
        except TimeoutError:
            return List()

        finally:
            self.raw.setForceStart(False)

    @property
    def enabled_files(self) -> List[TorrentFile]:
        return self.files.filtered(lambda f: f.enabled)

    #===================================================

    size: str = ""
    url : str = ""

    @property
    def hash(self) -> str:
        if self.raw:
            return self.raw.hash
        else:
            return self._hash

    _hash: str = None

    @property
    def name(self) -> str:
        self.refresh()
        if self.raw:
            return self.raw.name
        else:
            return self._name

    _name: str = None

    @property
    def seeders(self) -> int:
        self.refresh()
        if self.raw:
            return self.raw.num_complete
        else:
            return self._seeders
    
    _seeders: int = None
    
    @property
    def leechers(self) -> int:
        self.refresh()
        if self.raw:
            return self.raw.num_incomplete
        else:
            return self._leechers
    
    _leechers: int = None
    
    #===================================================

    @property
    def errored(self) -> bool:
        self.refresh()
        return self.raw.state_enum.is_errored
    
    @property
    def downloading(self) -> bool:
        self.refresh()
        return self.raw.state_enum.is_downloading

    @property
    def exists(self) -> bool:
        self.refresh()
        return len(qbit.torrents_info(torrent_hashes=self.hash)) > 0

    #===================================================

    @property
    def _tlist(self):
        self.refresh()
        return qbit.torrents_info(torrent_hashes=self.hash)

    def stop(self, rm_files:bool=True) -> None:
        self.refresh()
        return self.raw.delete(delete_files=rm_files)

    @Log.on_call
    def start(self):

        if not self.exists:

            qbit.torrents_add(self.url)
            
            to = qbit._timeout()

            while self.raw is None:
                self.refresh()
                to.check()

        return self

    #===================================================
