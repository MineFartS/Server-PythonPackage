from qbittorrentapi import TorrentDictionary
from functools import cached_property
from ...functools import copy_attrs
from ...terminal import Log

from .qbit import qBitTorrent as qbit
from .file import TorrentFile
from ...json import List

class Torrent(TorrentDictionary):

    def __init__(self,
        tdict: None | TorrentDictionary
    ) -> None:
        if tdict:
            self._load(tdict)

    def _load(self, tdict:TorrentDictionary):
        from ...pc import Path
        self.stop = tdict.delete
        self.path = Path(tdict.save_path)

        copy_attrs(tdict, self)

    def __repr__(self) -> str:
        from ...classtools import loc
        from ...text import abbr

        return f"<Torrent '{abbr(num=30, string=self.name)}' @{loc(obj=self)}>"

    #===================================================

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
        return List(TorrentFile(self, f) for f in super().files)

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

    seeders: int
    leechers: int
    size: str
    name: str

    #===================================================

    @Log.on_call
    def start(self) -> None:

        torrent = qbit.by_hash(self.hash)

        if torrent is None:

            qbit.torrents_add(self.url)

            self._load(qbit.by_hash(self.hash))

    #===================================================
