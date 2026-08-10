from ...functools.cache.prop import cached_property
from typing import TYPE_CHECKING, Literal
from .qbit import qBitTorrent as qbit
from dataclasses import dataclass
from .file import TorrentFile
from ...terminal import Log

if TYPE_CHECKING:
    from qbittorrentapi import TorrentDictionary
    from ...time import from_stamp
    from ...pc.Path import Path

class TorrentNotFoundError(Exception): ...

@dataclass
class Torrent:

    hash: str

    size: str = ""
    url : str = ""
    uploaded: 'None|from_stamp' = None
    type: None|Literal['Show', 'Movie', 'Episode'] = None

    #===================================================

    def __repr__(self) -> str:
        from ...functools import loc
        from ...text import abbr

        return f"<Torrent '{abbr(30, self.name)}' @{loc(self)}>"
    
    __str__ = __repr__

    def __format__(self, spec) -> str:
        return str(self).__format__(spec)
    
    #===================================================

    @property
    def raw(self) -> TorrentDictionary:
        from ...text import similarity

        for torr in qbit.torrents_info():
            if similarity(self.hash, torr.hash) > .95:
                return torr

        raise TorrentNotFoundError(self)

    #===================================================

    @cached_property
    @Log.on_call
    def files(self) -> tuple[TorrentFile, ...]:

        to = qbit._timeout()

        self.raw.setForceStart(True)

        try:
            
            while len(self.raw.files) == 0:
                to.check()

            return tuple(TorrentFile(self, f.id) for f in self.raw.files)
        
        except TimeoutError, TorrentNotFoundError:
            return ()

        finally: 
            if self.exists: self.raw.setForceStart(False)

    @property
    def enabled_files(self) -> tuple[TorrentFile, ...]:
        return tuple(filter(
            lambda f: f.enabled, 
            self.files
        ))

    #===================================================

    @cached_property
    def name(self) -> str:
        return self.raw.name.strip('\n')

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
        try:
            self.raw
            return True
        except TorrentNotFoundError:
            return False
    
    @cached_property
    def path(self) -> 'Path':
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
    def start(self) -> None:

        try:
            self.raw.recheck()
        except TorrentNotFoundError:
            qbit.torrents_add(self.url)
        
        to = qbit._timeout()

        while True:
            try: 
                self.raw
                return
            except TorrentNotFoundError: 
                to.check()

    #===================================================

    def __getstate__(self):
        return {
            'hash': self.hash,
            'size': self.size,
            'url': self.url,
            'name': self.name,
            'seeders': self.seeders,
            'leechers': self.leechers,
            'uploaded': self.uploaded,
            'type': self.type
        }

    #===================================================

