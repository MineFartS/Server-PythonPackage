from typing import TYPE_CHECKING
from functools import partial

if TYPE_CHECKING:
    from .pc import Path

#=================================

def __FFMPEG(name:str) -> 'Path':
    from .file import temp, ZIP
    from .web import download
    from .terminal import Log

    # Declare 'Ffmpeg.exe' location
    exe = temp(
        name = name,
        ext = 'exe',
        id = '0'
    )

    # Check if 'Ffmpeg.exe' does not exist
    if exe.exists:

        Log.VERB(f'{name}.exe Exists')

    else:

        Log.VERB(f'Downloading: {name}.exe')

        # Declare path for 'ffmpeg' zipfile
        zipfile = temp('ffmpeg', 'zip')
        """ffmpeg-release-essentials.zip"""

        # Download ffmpeg zipfile
        download(
            url = 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip',
            path = zipfile
        )

        # Open zipfile as an 'ZIP' object
        zip = ZIP(zipfile)

        # Search for 'ffmpeg.exe' in zipfile contents
        for f in zip.search(f'{name}.exe'):

            # Extract 'ffmpeg.exe' to location declared earlier
            zip.extractFile(
                file = f,
                savepath = exe
            )

            break

    return exe

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