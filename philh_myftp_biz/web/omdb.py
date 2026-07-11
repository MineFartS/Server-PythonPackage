from ..functools import TransitoryCache
from typing import NoReturn, Literal
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
    Released: 'from_stamp|None' = None

@singleton
class Tmdb:
    """https://api.themoviedb.org/"""

    key = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjYjg3MDhlNGRhZDkxOTI5N2Y2YWExZmNjN2NkYjMzYyIsIm5iZiI6MTc4MzUxOTM2Mi41MTgwMDAxLCJzdWIiOiI2YTRlNTg4MmNjNDg5MDY0MjJmOTBhOGIiLCJzY29wZXMiOlsiYXBpX3JlYWQiXSwidmVyc2lvbiI6MX0.mZvPMjqmMyNlBoY-wJsWQMruep92MwJqIJ35M65gMSI"
    
    url = URL("https://api.themoviedb.org/3/")
    url.headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {key}"
    }
    
    def get(self, path:str, **params) -> dict:
        try:
            return self.url.child(path).get(params).json()
        except TimeoutError:
            return {}

@singleton
class Omdb:
    """https://omdbapi.com/"""

    url = URL('https://www.omdbapi.com/')

    key: Literal['dc888719','2e0c4a98'] = 'dc888719'

    def get(self, **params) -> NoReturn | dict:

        data: dict = self.url.get({**params, 'apikey':self.key}).json()

        if 'Error' not in data:
            return data
        
        elif 'not found!' in data['Error']:
            raise NameError()
        
        else:
            raise ConnectionAbortedError(data['Error'])

    def movie(self,
        title: str,
        year: int
    ) -> None | MovieData:
        """Get details of a movie"""
        from ..time import from_string

        r = self.get(t=title, y=year)

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
        from ..time import from_string
        
        # Request raw list of seasons
        r1 = self.get(t=title, y=year)

        # Create new 'Show' obj
        show = ShowData(
            Seasons = {},
            Title = title,
            Year = year
        )

        try:
            tmdb_id: list[dict] = Tmdb.get(
                path = f'/find/{r1['imdbID']}', 
                external_source = 'imdb_id'
            ) ['tv_results'] [0] ['id']
        except IndexError as e:
            raise NameError() from e
        
        # Iter through all seasons by #
        for s in range(1, int(r1['totalSeasons'])+1):

            r2: dict = Tmdb.get(f'/tv/{tmdb_id}/season/{s}')

            show.Seasons [f'{s:02d}'] = {}

            # Iterate through the episodes in the season
            for e in r2.get('episodes', []):

                episode = EpisodeData(
                    Title = e['name'],
                    Number = e['episode_number']
                )
                
                try:
                    episode.Released = from_string(e['air_date'])
                except TypeError:
                    episode.Released = None

                show.Seasons [f'{s:02d}'] [f'{episode.Number:02}'] = episode

        return show
