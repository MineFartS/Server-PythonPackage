from ...functools import TransitoryCache, singleton
from typing import TYPE_CHECKING
from ...terminal import Log
from ...web import URL

if TYPE_CHECKING:
    from ...array import List
    from ..driver import Driver
    from .magnet import Magnet

@singleton
class thePirateBay:

    url = URL("https://thepiratebay11.com/search/")
    driver: 'Driver' = None

    def search(self, *queries:str) -> List[Magnet]:
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

    def rsearch(self, query:str) -> list[Magnet]:
        """Search thePirateBay for magnets"""
        from .magnet import Magnet
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
        
        magnets: list[Magnet] = []

        # Iter from 0 to # of lines
        for x in range(0, self.driver.run('return lines.length')):

            _run = lambda c: self.driver.run(f'return lines[{x}]{c}')

            try:

                # Yield a magnet instance
                magnets += [Magnet(

                    name = _run(".children[1].textContent"),

                    seeders = int(_run(".children[5].textContent")),

                    leechers = int(_run(".children[6].textContent")),

                    url = _run(".children[3].children[0].children[0].href"),
                    
                    size = Size.to_bytes(_run(".children[4].textContent"))

                )]

            except KeyError, RuntimeError:
                Log.VERB(exc_info=True)

        return magnets
