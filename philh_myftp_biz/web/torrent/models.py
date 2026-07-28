from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..torrent import Torrent
    from ...time import from_stamp

@dataclass(kw_only=True)
class MediaData:
    
    Title: str
    Torrent: 'None|Torrent' = None
    Released: 'None|from_stamp' = None

    @property
    def Year(self) -> None|int:
        return self.Released and self.Released.year

@dataclass
class MovieData(MediaData):
    ...

@dataclass
class ShowData(MediaData):
    Seasons: dict[str, dict[str, 'EpisodeData']]

@dataclass
class EpisodeData(MediaData):
    Number: int
