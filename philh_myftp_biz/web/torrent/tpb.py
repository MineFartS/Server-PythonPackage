from ...functools import singleton
from typing import TYPE_CHECKING
from ...terminal import Log
from ...web import URL

if TYPE_CHECKING:
    from ...array import List
    from ..driver import Driver
    from .magnet import Torrent

@singleton
class thePirateBay:

    url = URL("https://thepiratebay11.com/search/")
    driver: 'Driver' = None

    def search(self, *queries:str) -> List[Torrent]:
        """Search thePirateBay for magnets"""
        from ...array import List
        from ... import VERBOSE

        magnets = List()

        VERBOSE.pause()

        for q in queries:
            magnets += self.rsearch(q)
            magnets += self.rsearch(q.replace('.', '').replace("'", ''))
            magnets += self.rsearch(q.replace('.', ' ').replace("'", ' '))

        VERBOSE.resume()

        magnets.flatten()
        magnets.uniquify()

        return magnets

    def rsearch(self, query:str) -> list[Torrent]:
        """Search thePirateBay for magnets"""
        from urllib.parse import urlparse, parse_qs
        from .magnet import Torrent
        from ...db import Size

        if self.driver is None:
            self.driver = Driver()

        # Open the search in a url
        self.driver.open(
            url = self.url.child(query)
        )

        # Set driver var 'lines' to a list of lines
        try:
            self.driver.run("window.lines = document.getElementById('searchResult').children[1].children")
        except RuntimeError:
            return []
        
        magnets: list[Torrent] = []

        # Iter from 0 to # of lines
        for x in range(0, self.driver.run('return lines.length')):
            

            _run = lambda c: self.driver.run(f'return lines[{x}]{c}')

            try:

                # Yield a magnet instance
                t = Torrent(None)
                t.name = _run(".children[1].textContent")
                t.seeders = int(_run(".children[5].textContent"))
                t.leechers = int(_run(".children[6].textContent"))
                t.size = Size.to_bytes(_run(".children[4].textContent"))

                url = _run(".children[3].children[0].children[0].href")

                XT: str = parse_qs(urlparse(url).query)['xt'][0]
                if XT.startswith('urn:btih:'): # v1
                    t.hash = XT[len('urn:btih:'):].lower()
                elif XT.startswith('urn:btmh:'): # v2
                    t.hash = XT[len('urn:btmh:'):].lower()

                magnets += [t]

            except KeyError, RuntimeError:
                Log.VERB(exc_info=True)

        return magnets
