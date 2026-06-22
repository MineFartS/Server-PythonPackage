from ..classtools import singleton, bylazy
from typing import Literal, Generator
from functools import cached_property

from .Path import Path, PathPair
#========================================================

cwd = lambda: Path('.')
"""Get the Current Working Directory"""

def relscan(
    src: Path,
    dst: Path
) -> Generator[PathPair]:
    """
    Relatively Scan two directories

    EXAMPLE:

    C:/ - |
    (src) |
          | - Child1

    relscan(Path('C:/'), Path('D:/')) -> [{
        'src': Path('C:/Child1')
        'dst': Path('D:/Child1')
    }]
    """
    from ..classtools import SharedBuffer
    from shutil import copytree
    from ..process import Thread

    buff = SharedBuffer()
    
    # Copytree dry run
    t = Thread(

        func = copytree,

        src = str(src),
        dst = str(dst), 

        dirs_exist_ok = True,
        
        # Append paths to list instead of directly copying
        copy_function = lambda s, d, **_: buff.add(PathPair(s, d))

    )

    buff.stop_when = lambda: not t.running

    yield from buff

#========================================================
# NAME

from socket import gethostname
NAME = bylazy(gethostname)

#=================================
# OS

@bylazy
def OS() -> Literal['windows', 'unix']:
    from os import name

    match name:

        case 'nt':
            return 'windows'
        
        case _:
            return 'unix'

#=================================
# DIRs

@singleton
class loc:

    @property
    def temp(self) -> Path:
        from tempfile import gettempdir

        SERVER = Path('E:/__temp__/')

        if SERVER.exists and (NAME == 'PC-1'):
            return SERVER
        else:
            return Path(gettempdir())

    @cached_property
    def script(self) -> Path:
        from ..terminal import main_module

        return Path(main_module().__file__).parent

    @cached_property
    def cache(self) -> Path:

        path = self.script.child('/__pycache__/')

        path.mkdir()

        return path
    
    @cached_property
    def logs(self) -> Path:

        path = self.script.child('/__pylogs__/')

        path.mkdir()

        return path

#========================================================