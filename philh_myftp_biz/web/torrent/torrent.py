from qbittorrentapi import TorrentDictionary
from ...functools import cached_property
from .qbit import qBitTorrent as qbit
from dataclasses import dataclass
from .file import TorrentFile
from ...terminal import Log
from typing import ClassVar
from ...pc.Path import Path
from ...json import List

@dataclass
class Torrent:

    hash: str

    size: ClassVar[str] = ""
    url : ClassVar[str] = ""

    #===================================================

    def __repr__(self) -> str:
        from ...classtools import loc
        from ...text import abbr

        return f"<Torrent '{abbr(30, self.name)}' @{loc(self)}>"
    
    __str__ = __repr__

    def __format__(self, spec) -> str:
        return str(self).__format__(spec)
    
    #===================================================

    @property
    def raw(self) -> TorrentDictionary | None:
        for torr in qbit.torrents_info():
            if torr.hash == self.hash:
                return torr

    #===================================================

    @cached_property
    @Log.on_call
    def files(self) -> List[TorrentFile]:

        to = qbit._timeout()

        self.raw.setForceStart(True)

        try:
            
            while len(self.raw.files) == 0:
                to.check()

            files = []

            for f in self.raw.files:
                files += [TorrentFile(self, f.id)]

            return List(files)
        
        except TimeoutError:
            return List()

        finally:
            self.raw.setForceStart(False)

    @property
    def enabled_files(self) -> List[TorrentFile]:
        return self.files.filtered(lambda f: f.enabled)

    #===================================================

    @cached_property
    def name(self) -> str:
        return self.raw.name

    @cached_property
    def seeders(self) -> int:
        return self.raw.num_complete
    
    @cached_property
    def leechers(self) -> int:
        return self.raw.num_incomplete

    @property
    def errored(self) -> bool:
        return self.raw.state_enum.is_errored
    
    @property
    def downloading(self) -> bool:
        return self.raw.state_enum.is_downloading

    @property
    def exists(self) -> bool:
        return self.raw != None
    
    @cached_property
    def path(self) -> Path:
        from ...pc import Path
        return Path(self.raw.save_path)

    @property
    def finished(self) -> None | bool:
        state = self.raw.state_enum
        return (state.is_uploading or state.is_complete)

    #===================================================

    @Log.on_call
    def stop(self, rm_files:bool=True) -> None:
        return self.raw.delete(delete_files=rm_files)

    @Log.on_call
    def start(self):

        if self.raw is None:
            qbit.torrents_add(self.url)
        
        to = qbit._timeout()

        while self.raw is None:
            to.check()

    #===================================================
