from ...functools import TransitoryCache 
from typing import TYPE_CHECKING
from ...terminal import Log
from ...web import URL

if TYPE_CHECKING:
    from .torrent import Torrent
    from ..driver import Driver
    from .name import Weights
    from ...json import List

url = URL("https://thepiratebay11.com/search/")

driver: Driver = None

cache = TransitoryCache('tpb')

@Log.on_call
def search(
    *queries:str, 
    weights: 'None|Weights' = None
) -> List[Torrent]:
    """Search thePirateBay for magnets"""
    from ...json import List
    from ... import VERBOSE

    torrents: list[Torrent] = []

    VERBOSE.pause()

    for q in queries:
        torrents += _search(q)
        torrents += _search(q.replace('.', '').replace("'", ''))
        torrents += _search(q.replace('.', ' ').replace("'", ' '))

    VERBOSE.resume()

    if weights:
        torrents = filter(
            lambda t: weights.parse(t.name),
            torrents
        )

    return List(torrents)

def _search(query:str) -> list[Torrent]:
    """Search thePirateBay for magnets"""
    from urllib.parse import urlparse, parse_qs
    from .torrent import Torrent
    from ...db import Size

    global driver, url, cache

    if cache[query]:
        return cache[query] # pyright: ignore[reportReturnType]

    if driver is None:
        driver = Driver()

    driver.open(url.child(query))

    # Set driver var 'lines' to a list of lines
    try:
        driver.run("window.lines = document.getElementById('searchResult').children[1].children")
    except RuntimeError:
        return []
    
    torrents = []

    # Iter from 0 to # of lines
    for x in range(0, driver.run('return lines.length')):

        _run = lambda c: driver.run(f'return lines[{x}]{c}')

        try:

            t = Torrent(hash=None)

            t.url = _run(".children[3].children[0].children[0].href")
            t.size = Size.to_bytes(_run(".children[4].textContent"))
            t.name = _run(".children[1].textContent")
            t.seeders = int(_run(".children[5].textContent"))
            t.leechers = int(_run(".children[6].textContent"))

            XT: str = parse_qs(urlparse(t.url).query)['xt'][0]
            if XT.startswith('urn:btih:'): # v1
                t.hash = XT[len('urn:btih:'):].lower()
            elif XT.startswith('urn:btmh:'): # v2
                t.hash = XT[len('urn:btmh:'):].lower()

            torrents += [t]

        except (KeyError, RuntimeError):
            Log.VERB(exc_info=True)

    cache[query] = torrents

    return torrents

