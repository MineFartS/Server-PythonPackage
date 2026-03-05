from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..time import from_stamp

class Movie:
    Title: str
    Year: int
    Released: 'from_stamp'

class Show:
    Title: str
    Year: int
    Seasons: dict[str, dict[str, Episode]]

class Episode:
    Title: str
    Released: 'from_stamp|None'
    Number: int

class Omdb:
    """
    OMDB API

    'https://www.omdbapi.com/{url}'
    """

    def __init__(self,
        key: int = 0
    ) -> None:
        
        match key:

            case 0: self.key = 'dc888719'

            case 1: self.key = '2e0c4a98'

            case _: raise KeyError()

    def movie(self,
        title: str,
        year: int
    ) -> None | Movie:
        """
        Get details of a movie
        """
        from ..time import from_string
        from ..json import Dict
        from ..web import get

        response = get(
            url = 'https://www.omdbapi.com/',
            params = {
                't': title,
                'y': year,
                'apikey': self.key
            }
        )

        r: Dict[str] = Dict(response.json())

        if bool(r['Response']):
            
            if r['Type'] == 'movie':

                movie = Movie()

                movie.Title = r['Title'] # pyright: ignore[reportAttributeAccessIssue]
                movie.Year = int(r['Year'])
                movie.Released = from_string(r['Released'])

                return movie

    def show(self,
        title: str,
        year: int
    ) -> None | Show:
        """
        Get details of a show
        """
        from ..time import from_string
        from ..json import Dict
        from ..web import get

        # Request raw list of seasons
        req = get(
            url = 'https://www.omdbapi.com/',
            params = {
                't': title,
                'y': year,
                'apikey': self.key
            }
        )

        # Parse the response
        pres: Dict[str] = Dict(req.json())

        # If an error is given
        if pres['Error']:

            # Raise an error with the given message
            raise ConnectionAbortedError(pres['Error'])

        # If a response of 'series' type is given
        elif pres['Type'] == 'series':

            # Create new 'Show' obj
            show = Show()

            #
            show.Seasons = {}

            # Set attributes of 'Show' obj
            show.Title = title
            show.Year = year

            # Iter through all seasons by #
            for s in range(1, int(pres['totalSeasons'])+1):

                show.Seasons[f'{s:02d}'] = {}

                # Request season details and parse response
                pres2: dict[str, str] = get(
                    url = self.__url,
                    params = {
                        't': title,
                        'y': year,
                        'Season': s,
                        'apikey': self.key
                    }
                ).json()

                # Iterate through the episodes in the season details
                for e in pres2['Episodes']:

                    # Create new 'Episode' obj
                    episode = Episode()

                    # Set attributes of 'Episode' obj
                    episode.Title = e['Title']
                    episode.Number = int(e['Episode'])
                    
                    # If the show has a release date, then parse the date
                    try:
                        episode.Released = from_string(e['Released'])
                    except TypeError:
                        episode.Released = None

                    show.Seasons [f'{s:02d}'] [e['Episode'].zfill(2)] = episode

            # Return the 'Show' obj
            return show
