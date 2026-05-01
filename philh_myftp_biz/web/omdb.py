from typing import TYPE_CHECKING, NoReturn, Literal
from ..functools import TransitoryCache
from ..classtools import singleton
from ..json import Dict
from ..web import URL

if TYPE_CHECKING:
    from ..time import from_stamp

class MovieData:
    Title: str
    Year: int
    Released: 'from_stamp'

class ShowData:
    Title: str
    Year: int
    Seasons: dict[str, dict[str, EpisodeData]]

class EpisodeData:
    Title: str
    Released: 'from_stamp|None'
    Number: int

class MediaNotFoundError(Exception): ...

@singleton
class Omdb:
    """
    OMDB API

    'https://www.omdbapi.com/{url}'
    """

    url = URL('https://www.omdbapi.com/')

    _keys = [
        'dc888719',
        '2e0c4a98'
    ]

    key: Literal[*_keys] = 'dc888719'

    mcache: TransitoryCache[MovieData] = TransitoryCache('m', expire=36000)

    scache: TransitoryCache[ShowData]  = TransitoryCache('s', expire=36000)

    def _get(self, params:dict) -> NoReturn | Dict[str]:
        from ..json import Dict
        from .. import VERBOSE

        VERBOSE.pause()

        params['apikey'] = self.key

        response = self.url.get(params)

        data = Dict(response.json())

        VERBOSE.resume()

        # If an error is given
        if data['Error']:
            
            if 'Movie not found!' in data['Error']:
                raise MediaNotFoundError()
            
            else:
                raise ConnectionAbortedError(data['Error'])

        else:
            return Dict(response.json())

    def movie(self,
        title: str,
        year: int
    ) -> None | MovieData:
        """Get details of a movie"""
        from ..time import from_string

        params = {
            't': title,
            'y': year
        }

        if params in self.mcache:
            return self.mcache[params]

        r = self._get({
            't': title,
            'y': year
        })

        if bool(r['Response']) and (r['Type'] == 'movie'):
            
            movie = MovieData()

            movie.Title = r['Title']
            movie.Year = int(r['Year'])
            movie.Released = from_string(r['Released'])

        else:
            movie = None
            
        self.mcache[params] = movie
        return None

    def show(self,
        title: str,
        year: int
    ) -> None | ShowData:
        """Get details of a show"""
        from ..time import from_string

        params = {
            't': title,
            'y': year
        }

        if params in self.scache:
            return self.scache[params]

        # Request raw list of seasons
        r1 = self._get(params)

        # Create new 'Show' obj
        show = ShowData()

        show.Seasons = {}

        # Set attributes of 'Show' obj
        show.Title = title
        show.Year = year

        # Iter through all seasons by #
        for s in range(1, int(r1['totalSeasons'])+1):

            show.Seasons[f'{s:02d}'] = {}

            # Request season details and parse response
            r2 = self._get({
                't': title,
                'y': year,
                'Season': s
            })

            # Iterate through the episodes in the season details
            for e in r2['Episodes']:

                # Create new 'Episode' obj
                episode = EpisodeData()

                # Set attributes of 'Episode' obj
                episode.Title = e['Title']
                episode.Number = int(e['Episode'])
                
                # If the show has a release date, then parse the date
                try:
                    episode.Released = from_string(e['Released'])
                except TypeError:
                    episode.Released = None

                show.Seasons [f'{s:02d}'] [e['Episode'].zfill(2)] = episode

        self.scache[params] = show

        # Return the 'Show' obj
        return show
