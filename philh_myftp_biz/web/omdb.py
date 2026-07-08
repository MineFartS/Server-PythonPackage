from typing import NoReturn, Literal, ClassVar
from ..functools import TransitoryCache
from ..classtools import singleton
from dataclasses import dataclass
from ..time import from_stamp
from ..web import URL

@dataclass
class MovieData:
    Title: str
    Year: int
    Released: 'from_stamp'

@dataclass
class ShowData:
    Title: str
    Year: int
    Seasons: dict[str, dict[str, 'EpisodeData']]

@dataclass
class EpisodeData:
    Title: str
    Number: int
    Released: ClassVar['from_stamp|None']

class MediaNotFoundError(Exception): ...

@singleton
class Omdb:
    """
    OMDB API

    'https://www.omdbapi.com/{url}'
    """

    url = URL('https://www.omdbapi.com/')

    key: Literal['dc888719','2e0c4a98'] = 'dc888719'

    _cache: TransitoryCache[dict] = TransitoryCache('omdb', expire=36000)

    def _get(self, **params) -> NoReturn | dict:
        from .. import VERBOSE

        if params not in self._cache:
            VERBOSE.pause()
            self._cache[params] = self.url.get({**params, 'apikey':self.key}).json()
            VERBOSE.resume()

        data: dict = self._cache[params]

        if 'Error' not in data:
            return data
        
        elif 'not found!' in data['Error']:
            raise MediaNotFoundError()
        
        else:
            raise ConnectionAbortedError(data['Error'])

    def movie(self,
        title: str,
        year: int
    ) -> None | MovieData:
        """Get details of a movie"""
        from ..time import from_string

        r = self._get(t=title, y=year)

        if bool(r['Response']) and (r['Type'] == 'movie'):
            return MovieData(
                Title = r['Title'],
                Year = int(r['Year']),
                Released = from_string(r['Released'])
            )

    def show(self,
        title: str,
        year: int
    ) -> None | ShowData:
        """Get details of a show"""
        from collections import defaultdict
        from ..time import from_string

        # Request raw list of seasons
        r1 = self._get(t=title, y=year)

        # Create new 'Show' obj
        show = ShowData(
            Seasons = defaultdict(dict),
            Title = title,
            Year = year
        )

        # Iter through all seasons by #
        for s in range(1, int(r1['totalSeasons'])+1):

            # Request season details
            r2 = self._get(t=title, y=year, Season=s)

            # Iterate through the episodes in the season
            for e in r2['Episodes']:

                episode = EpisodeData(
                    Title = e['Title'],
                    Number = int(e['Episode'])
                )
                
                try: # Parse the release date
                    episode.Released = from_string(e['Released'])
                except TypeError:
                    episode.Released = None

                show.Seasons [f'{s:02d}'] [e['Episode'].zfill(2)] = episode

        return show
