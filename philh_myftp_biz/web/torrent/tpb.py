from typing import TYPE_CHECKING, Generator
from .torrent import Torrent
from ...terminal import Log
from ..url import URL

if TYPE_CHECKING:
    from ..driver import Driver

url = URL("https://thepiratebay11.com/search/")

driver: Driver = None

@Log.on_call
def search(*queries:str) -> Generator[Torrent]:
    """Search thePirateBay for magnets"""

    for q in queries:
        yield from _search(q)
        yield from _search(q.replace('.', '').replace("'", ''))
        yield from _search(q.replace('.', ' ').replace("'", ' '))

def _search(query:str) -> Generator[Torrent]:
    """Search thePirateBay for magnets"""
    from urllib.parse import urlparse, parse_qs
    from ...time import from_string
    from .name import NameParser
    from .torrent import Torrent
    from ...db import Size

    global driver, url

    if driver is None:
        driver = Driver()

    driver.open(url.child(query))

    # Set driver var 'lines' to a list of lines
    try:
        driver.run("window.lines = document.getElementById('searchResult').children[1].children", False)
    except RuntimeError:
        return []

    # Iter from 0 to # of lines
    for x in range(0, driver.run('return lines.length')):

        _run = lambda c: driver.run(f'return lines[{x}].children{c}', False)

        try:

            t = Torrent(hash=None)

            t.url = _run("[3].children[0].children[0].href")
            t.size = Size.to_bytes(_run("[4].textContent"))
            t.name = _run("[1].textContent")
            t.seeders = int(_run("[5].textContent"))
            t.leechers = int(_run("[6].textContent"))

            try:
                t.uploaded = from_string(_run("[2].textContent"))
            except TypeError:
                pass
            
            _type = _run("[0].textContent").lower()
            if 'movie' in _type:
                t.type = "Movie"
            elif NameParser(t.name).episode:
                t.type = 'Episode'
            elif 'show' in _type:
                t.type = 'Show'
            
            XT: str = parse_qs(urlparse(t.url).query)['xt'][0]
            if XT.startswith('urn:btih:'): # v1
                t.hash = XT[len('urn:btih:'):].lower()
            elif XT.startswith('urn:btmh:'): # v2
                t.hash = XT[len('urn:btmh:'):].lower()

            yield t

        except (KeyError, RuntimeError):
            Log.VERB(exc_info=True)

