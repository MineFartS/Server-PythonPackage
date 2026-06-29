from typing import TYPE_CHECKING
from functools import partial

if TYPE_CHECKING:
    from .pc import Path

#=================================

def __FFMPEG(name:str) -> 'Path':
    from .file import temp, ZIP
    from .web import URL

    exefile = temp(name, 'exe', 0)

    zipurl = URL("https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip")

    zipfile = temp('ffmpeg', 'zip', 0)
    zipurl.cache(zipfile)

    # Open zipfile as an 'ZIP' object
    zip = ZIP(zipfile)

    # Search for exefile in zipfile contents
    member = zip.search(f'{name}.exe')[0]

    # Extract 'ffmpeg.exe' to location declared earlier
    zip.extractFile(
        member = member,
        path = exefile
    )

    return exefile

FFMPEG : partial[Path] = partial(__FFMPEG, 'ffmpeg')

FFPROBE: partial[Path] = partial(__FFMPEG, 'ffprobe')

#=================================

def COOKIES() -> 'Path':
    from http.cookiejar import MozillaCookieJar
    from browser_cookie3 import firefox
    from .file import temp

    # Declare 'cookies.txt' location
    CookiesTXT = temp(name='cookies', ext='txt', id='0')

    # Check if 'cookies.txt' does not exist
    if not CookiesTXT.exists:

        # Create Empty CookieJar
        CJ = MozillaCookieJar(filename=str(CookiesTXT))

        # Populate the CookieJar with cookies from FireFox
        for cookie in firefox():
            CJ.set_cookie(cookie=cookie)

        # Save the cookies to 'cookies.txt'
        CJ.save()

    return CookiesTXT

#=================================

def install_requirements(
    txtfile: Path = None
) -> None:
    from .process import RunHidden
    from .pc import loc

    if txtfile is None:
        txtfile = loc.script.child('requirements.txt')

    RunHidden(
        args = ['pip', 'install', '-r', txtfile],
        terminal = 'pym'
    )

#=================================