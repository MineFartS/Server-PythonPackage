from qbittorrentapi import TorrentDictionary
from functools import cached_property
from ...terminal import Log

from .qbit import qBitTorrent as qbit
from .file import TorrentFile
from ...json import List

class Torrent(TorrentDictionary):

    def __init__(self) -> None:
        pass

    def __repr__(self) -> str:
        from ...classtools import loc
        from ...text import abbr

        return f"<Torrent '{abbr(30, self.name)}' @{loc(self)}>"
    
    __str__ = __repr__

    def __format__(self, spec):
        return str(self).__format__(spec)

    #===================================================

    @property
    def path(self):
        from ...pc import Path
        return Path(self.save_path)

    @property
    def finished(self) -> None | bool:
        return (self.state_enum.is_uploading or self.state_enum.is_complete)

    @property
    def stalled(self) -> None | bool:
        return (self.state_enum.value == 'stalledDL')

    #===================================================

    @cached_property
    def files(self) -> List[TorrentFile]:

        #=====================
        
        to = qbit._timeout()

        self.setForceStart(True)

        while len(super().files) == 0:
            to.check()

        self.setForceStart(False)

        #=====================

        files = list(super().files)

        for f in files:
            f.__class__ = TorrentFile
            f.torrent = self

        return List(files) # pyright: ignore[reportReturnType]

    @property
    def enabled_files(self) -> List[TorrentFile]:
        return self.files.filtered(lambda f: f.enabled)

    #===================================================

    def __setattr__(self, name:str, value):
        self.__dict__[name] = value

    def __getattr__(self, name:str):
        match name:

            case 'seeders':
                return getattr(self, 'num_complete', -1)
            
            case 'leechers':
                return getattr(self, 'num_incomplete', -1)
            
            case 'size' | 'name':
                return ""
            
            case "errored" | "downloading":
                try:
                    return getattr(self.state_enum, 'is_'+name)
                except AttributeError:
                    pass
            
            case _:
                return super().__getattribute__(name)

    seeders: int
    leechers: int
    size: str
    name: str
    url: str
    errored: None | bool
    downloading: None | bool

    #===================================================

    @property
    def exists(self) -> bool:
        return \
            hasattr(self, 'hash') and \
            len(qbit.torrents_info(torrent_hashes=self.hash)) > 0

    #===================================================

    def stop(self, rm_files:bool=True) -> None:
        return self.delete(delete_files=rm_files)

    @Log.on_call
    def start(self) -> Torrent:

        qbit.torrents_add(self.url)
        
        to = qbit._timeout()

        torrents = []

        while len(torrents) == 0:
            torrents = qbit.torrents_info(torrent_hashes=self.hash)
            to.check()

        torrents[0].__class__ = Torrent
        return torrents[0] # pyright: ignore[reportReturnType]

    #===================================================
