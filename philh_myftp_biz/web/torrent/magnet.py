from qbittorrentapi import TorrentDictionary
from functools import cached_property
from typing import Callable
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

        return f"<Torrent '{abbr(num=30, string=self.name)}' @{loc(obj=self)}>"

    #===================================================

    @property
    def path(self):
        from ...pc import Path
        return Path(self.save_path)

    @property
    def errored(self) -> bool:
        return self.state_enum.is_errored
    
    @property
    def downloading(self) -> bool:
        return self.state_enum.is_downloading

    @property
    def finished(self) -> None | bool:
        return (self.state_enum.is_uploading or self.state_enum.is_complete)

    @property
    def stalled(self) -> None | bool:
        return (self.state_enum.value == 'stalledDL')

    #===================================================
         
    def wait(self) -> None:

        to = qbit._timeout()

        self.setForceStart(True)

        while len(super().files) == 0:
            to.check()

        self.setForceStart(False)

    #===================================================

    @cached_property
    def files(self) -> List[TorrentFile]:

        items = List()

        for f in super().files:
            f.__class__ = TorrentFile
            items += f

        return items

    @property
    def enabled_files(self) -> List[TorrentFile]:
        return self.files.filtered(lambda f: f.enabled)

    #===================================================

    def __getattr__(self, name:str):
        match name:

            case 'seeders':
                return self.num_complete
            
            case 'leechers':
                return self.num_incomplete
            
            case 'size':
                return ""
            
            case 'stop':
                return self.delete

    seeders: int
    leechers: int
    size: str
    name: str
    url: str
    stop: Callable[[], None]

    #===================================================

    @Log.on_call
    def start(self) -> None | Torrent:

        qbit.torrents_add(self.url)
        
        torrents = self.torrents_info(torrent_hashes=self.hash)

        if len(torrents) > 0:
            t = torrents[0]
            t.__class__ = Torrent
            return t

    #===================================================
