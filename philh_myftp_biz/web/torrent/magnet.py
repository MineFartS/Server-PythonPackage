from qbittorrentapi import TorrentDictionary
from functools import cached_property
from ...functools import copy_attrs
from ...terminal import Log

from .qbit import qBitTorrent as qbit
from .file import TorrentFile
from ...json import List

class Torrent(TorrentDictionary):

    def __init__(self,
        tdict: TorrentDictionary
    ) -> None:
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

class Magnet(Torrent):

    def __init__(self,
        name: str = '',
        seeders: int = -1,
        leechers: int = -1,
        url: str = '',
        size: str = -1
    ) -> None:
        from urllib.parse import urlparse, parse_qs
        from .name import NameParser

        #===================================================

        # Get the first value of the 'xt' parameter
        XT: str = parse_qs(urlparse(url).query)['xt'][0]

        if XT.startswith('urn:btih:'): # v1
            self.hash = XT[len('urn:btih:'):].lower()
        
        elif XT.startswith('urn:btmh:'): # v2
            self.hash = XT[len('urn:btmh:'):].lower()

        #===================================================
        
        self.leechers = leechers
        self.seeders = seeders
        self.size  = size
        self.url = url

        #===================================================

        np = NameParser(name.lower().strip('\n'))

        self.name = np.name
        self.title = np.title
        self.season = np.season
        self.episode = np.episode
        self.year = np.year
        self.quality = np.quality

        #===================================================

    #===================================================

    @Log.on_call
    def start(self) -> None:

        torrent = qbit.by_hash(self.hash)

        if torrent is None:
            qbit.torrents_add(self.url)

        Torrent.__init__(self, 
            qbit, 
            qbit.by_hash(self.hash)
        )

        Torrent.start(self)

    def __repr__(self) -> str:
        from ...classtools import loc
        from ...text import abbr

        return f"<Magnet '{abbr(30, self.name)}' @{loc(self)}>"

    #===================================================
