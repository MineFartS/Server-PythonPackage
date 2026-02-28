from typing import Literal, Self, Generator, TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .time import from_stamp
    from pathlib import PurePath

from socket import gethostname as NAME # pyright: ignore[reportUnusedImport]

#========================================================

from os import name as __name

OS: Literal['windows', 'unix']

match __name:

    case 'nt':
        OS = 'windows'
    
    case _:
        OS = 'unix'

#========================================================

class Path:
    """
    File/Folder
    """

    def __init__(self,
        *input: 'str|PurePath'
    ) -> None:
        from pathlib import Path as libPath
        from os import path

        # ==================================

        if len(input) > 1:
            joined: str = path.join(*input)
            self.path = joined.replace('\\', '/')

        elif isinstance(input[0], Path):
            self.path = input[0].path

        elif hasattr(input[0], 'as_posix'):
            self.path = input[0].as_posix()

        else:
            self.path = libPath(input[0]).absolute().as_posix()

        # ==================================
        # Declare path string

        if self.path[0][-1] == '/':                
            self.path += '/'

        self.path: str = self.path.replace('\\', '/').replace('//', '/')
        """File Path with forward slashes"""

        # ==================================

        # Declare 'pathlib.Path' attribute
        self._libPath = libPath(self.path)

        # Link 'exists', 'isfile', & 'isdir' functions from 'self._libPath'
        self.exists = self._libPath.exists
        """Check if path exists"""

        self.isfile = self._libPath.is_file
        """Check if path is a file"""
        
        self.isdir = self._libPath.is_dir
        """Check if path is a folder"""

        # Declare 'set_access'
        self.set_access = _set_access(path=self)
        """Filesystem Access"""

        # Declare 'mtime'
        self.mtime = _mtime(path=self)
        """Modified Time"""

        # Declare 'visibility'
        self.visibility = _visibility(path=self)
        """Visibility"""

        # ==================================

        # Add trailing '/'
        if (not self.path.endswith('/')) and self.isdir():
            self.path += '/'

        # ==================================

    def chext(self, ext:str):
        """
        Returns an Path object with the same path, except with a different extension
        """
        if '.' in self.seg():
            path = self.path[:self.path.rfind('.')]
        else:
            raise TypeError("Path does not have an existing extension")
        
        return Path(path+'.'+ext)

    def ctime(self):
        from os import path
        from .time import from_stamp

        stamp = path.getctime(self.path)

        return from_stamp(stamp)

    def cd(self) -> '_cd':
        """
        Change the working directory to path
        
        If path is a file, then it will change to the file's parent directory
        """
        if self.isfile():
            return _cd(self.parent())
        else:
            return _cd(self)
    
    def ischild(self, parent:Path) -> bool:
        """
        Check if this path is a child or descendant of a parent directory
        """
        
        try:
            return self._libPath.is_relative_to(str(parent))
        
        except ValueError:
            return False
        
    def isparent(self, child:Path) -> bool:
        """
        Check if this path is a parent of ancestor of a path
        """
        return child.ischild(self)

    def isrelated(self, path:Path):
        """
        Check if this path is related to another
        
        ---
        Returns True is any of the following:
        - Is parent of
        - Is child of
        - Is same path
        """

        PARENT = self.isparent(path)
        CHILD  = self.ischild(path)
        SAME   = (self == path)

        return any([PARENT, CHILD, SAME])

    def resolute(self) -> Path:
        """
        Get path with Symbolic Links Resolved
        """
        return Path(self._libPath.resolve(strict=True))
    
    def child(self, *name:str) -> Path:
        """
        Get child of path
        
        Note: Will raise TypeError if path is a file
        """

        if self.isfile():
            raise TypeError("Parent path cannot be a file")
        
        elif len(name) > 1:
            return Path(self.path + '/'.join(name))
        
        elif name[0].startswith('/'):
            return Path(self.path + name[0][1:])
            
        else:
            return Path(self.path + name[0])

    def __str__(self) -> str:
        return self.path

    __repr__ = __str__
    
    def __format__(self, spec:str) -> str:
        return f'{self.path:{spec}}'

    def __eq__(self,
        other: Path|Any
    ) -> bool:

        if isinstance(other, Path):
            return (self.path == other.path)
        else:
            return False

    def islink(self) -> bool:
        """
        Check if path is Symbolic Link or Directory Junction
        """

        return (self._libPath.is_symlink() or self._libPath.is_junction())

    def size(self) -> int:
        """
        Get File Size

        Note: Will return TypeError is path is folder
        """
        from os import path

        if self.isfile():
            return path.getsize(self.path)
        else:
            raise TypeError("Cannot get size of a folder")

    def children(self) -> Generator[Path]:
        """
        Get children of current directory

        Curdir - |
                 | - Child
                 |
                 | - Child
        """
        for p in self._libPath.iterdir():
            yield Path(p)

    def descendants(self) -> Generator[Path]:
        """
        Get descendants of current directory

        Curdir - |           | - Descendant
                 | - Child - |
                 |           |
                 |           | - Descendant
                 |
                 | - Child - |
                             | - Descendant
        """
        for root, dirs, files in self._libPath.walk():
            for item in (dirs + files):
                yield Path(root, item)

    def isempty(self) -> bool:
        
        if self.isfile():
            raise TypeError('Cannot get children of a file')
        
        else:

            item = next(self.children(), None)

            return bool(item)

    def parent(self) -> Path:
        """
        Get parent of current path
        """ 
        return Path(self._libPath.parent.as_posix() + '/')

    def var(self,
        name: str
    ) -> '_var':
        """
        Get Variable Object for storing custom metadata
        """
        return _var(file=self, title=name)
    
    def sibling(self, item:str) -> Path:
        """
        Get sibling of current path

        CurPath - |
                  |
        Sibling - |
                  |
        """
        return self.parent().child(item)
    
    def ext(self) -> str|None:
        """
        Get file extension of path
        """

        seg: str = self.seg()

        if '.' in seg:

            return seg[seg.rfind('.')+1:].lower()

    def type(self) -> None | str:
        """
        Get mime type of path
        """
        from .db import MimeType

        return MimeType.Path(self)

    def delete(self) -> None:
        """
        Delete the current path
        """
        from .terminal import Log

        # If path is a directory
        if self.isdir():
            from shutil import rmtree as delete
        
        # If path is a file
        else:
            from os import remove as delete

        # If the path exists
        if self.exists():

            # Update Access
            self.set_access.full()

            Log.VERB(f'Deleting: {self=}')

            #            
            delete(self.path)

    def rename(self,
        dst: Path|str,
        overwrite: bool = True
    ) -> None:
        """
        Change the name of the current path
        """
        from os import rename

        src = self
        dst = Path(dst)

        if dst.ext() is None:
            dst.chext(self.ext())
        
        with src.cd():
            
            try:
                rename(src.path, dst.path)

            except FileExistsError:

                if overwrite:
                    dst.delete()
                    rename(src, dst)

                else:
                    raise FileExistsError(str(dst))

    def name(self) -> str:
        """
        Get the name of the current path

        Ex: 'C:/example.txt' -> 'example' 
        """

        name = self._libPath.name

        # Check if file has ext
        if self.ext():
            # Return name without ext
            return name[:name.rfind('.')]

        else:
            # Return filename
            return name

    def seg(self, i:int=-1) -> str:
        """
        Returns segment of path split by '/'
        (Ignores last slash on paths)

        EXAMPLES:
        
            Path('C:/example/test.log').seg(-1) -> 'test.log'

            Path('C:/example/').seg(-1) -> 'example'
        """
        
        if self.path[-1] == '/':
            path: str = self.path[:-1]
        else:
            path = self.path
        
        return path.split(sep='/') [i]

    def copy(
        self,
        dst: 'Path'
    ) -> None:
        """
        Copy the path to another location
        """
        from shutil import copyfile
        from .terminal import Log

        Log.VERB(
            f'Initializing Copier\n'+ \
            f'{self=}\n'+ \
            f'{dst=}'
        )

        files: list[dict[Literal['src', 'dst'], Path]] = []

        try:

            # If the source is a directory
            if self.isdir():

                files = relscan(self, dst)

            # If the source is file and destination is folder 
            elif dst.isdir():
                files = [{
                    'src': self, 
                    'dst': dst.child(self.seg())
                }]
                
            # If both the source and destination are files
            else:
                files = [{
                    'src': self, 
                    'dst': dst
                }]

            # Iter through source and destination pairs
            for file in files:

                Log.VERB(
                    f'Copying File\n'+ \
                    f'{file['src']=}\n'+ \
                    f'{file['dst']=}'
                )

                # Delete destination file
                file['dst'].delete()

                # Create the parent folder of the destination file
                mkdir(file['dst'].parent())

                # Copy the source file to the destination
                copyfile(
                    src = str(file['src']),
                    dst = str(file['dst'])
                )

            Log.VERB(
                f'Copy Completed\n'+ \
                f'{self=}\n'+ \
                f'{dst=}'
            )

        except Exception as e:

            # Delete destination paths
            for file in files:
                file['dst'].delete()

            raise OSError(f'Failed to copy \n"{self}" \nto \n"{dst}" ') from e

    def move(self,
        dst: Self
    ) -> None:
        """
        Move the path to another location
        """
        self.copy(dst)
        self.delete()

    def inuse(self) -> bool:
        """
        Check if path is in use by another process
        """
        from os import rename

        if self.exists():
            try:
                rename(self.path, self.path)
                return False
            except PermissionError:
                return True
        else:
            return False

    def open(self,
        mode: Literal['r', 'w', 'a', 'rb', 'wb', '+'] = 'r'
    ):
        """
        Open the current file

        Works the same as: open(self.Path)
        """
        return open(file=self.path, mode=mode)

    def relative(self, ancestor:Path) -> str:

        relpath = self._libPath.relative_to(other=ancestor.path)
        
        return relpath.as_posix()

class _cd:
    """
    Advanced Options for Change Directory
    """

    def __enter__(self):
        self.__via_with = True

    def __exit__(self, *_):
        if self.__via_with:
            self.back()

    def __init__(self, path:'Path'):
        
        self.__via_with = False

        self.__target = path

        self.open()

    def open(self) -> None:
        """
        Change CWD to the given path

        Saves CWD for easy return with cd.back()
        """
        from os import getcwd, chdir

        self.__back = getcwd()

        chdir(self.__target.path)

    def back(self) -> None:
        """
        Change CWD to the previous path
        """
        from os import chdir
        
        chdir(self.__back)

class _mtime:

    def __init__(self, path:Path):
        self.path = path

    def set(self,
        mtime: int | 'from_stamp' = None
    ):
        from .time import from_stamp
        from .time import now
        from os import utime
        
        if isinstance(mtime, from_stamp):
            mtime = mtime.unix

        if mtime:
            utime(self.path.path, (mtime, mtime))

        else:
            now = now().unix
            utime(self.path.path, (now, now))

    def get(self):
        from .time import from_stamp
        from os import path

        mtime = path.getmtime( str(self.path) )

        return from_stamp(mtime)

    def stopwatch(self):
        from .time import Stopwatch

        SW = Stopwatch()

        SW.start_time = self.get()
        
        return SW

class _var:

    def __init__(self,
        file: Path,
        title: str
    ):
        from .text import hex

        self.file = file
        self.title = title

        self.path = file.path + ':' + hex.encode(title)

        file.set_access.full()

    def read(self):
        from .text import hex

        try:
            value = open(self.path).read()
            return hex.decode(value)
        except OSError:
            return self.default
        
    def save(self, value:Any):
        from .text import hex
        
        try:

            m = _mtime(self.file).get()

            open(file=self.path, mode='w').write(
                hex.encode(value)
            )

            _mtime(path=self.file).set(mtime=m)
        
        except OSError as e:

            raise OSError(f"Error setting var '{self.title}' at '{self.file}'") from e

class _set_access:

    def __init__(self, path:'Path'):
        self.path = path

    def __paths(self) -> Generator['Path']:

        yield self.path

        if self.path.isdir():
            for path in self.path.descendants():
                yield path
    
    def readonly(self):
        from .terminal import Log
        from os import chmod

        for path in self.__paths():

            Log.VERB(f'Updating Access [READ ONLY]: {path}')
            
            chmod(str(path), 0o644)

    def full(self):
        from .terminal import Log
        from os import chmod

        for path in self.__paths():

            Log.VERB(f'Updating Access [FULL ACCESS]: {path}')

            chmod(str(path), 0o777)

class _visibility:
    
    def __init__(self, path:Path):
        self.path = path

    def hide(self) -> None:
        from win32con import FILE_ATTRIBUTE_HIDDEN
        from win32file import GetFileAttributes
        from win32api import SetFileAttributes
        from pywintypes import error

        self.path.set_access.full()

        attrs = GetFileAttributes(str(self.path))

        try:
            SetFileAttributes(
                str(self.path),
                (attrs | FILE_ATTRIBUTE_HIDDEN)
            )
        except error as e:
            raise PermissionError(*e.args)

    def show(self) -> None:
        from win32con import FILE_ATTRIBUTE_HIDDEN
        from win32file import GetFileAttributes
        from win32api import SetFileAttributes
        from pywintypes import error

        self.path.set_access.full()

        attrs = GetFileAttributes(str(self.path))

        try:
            SetFileAttributes(
                str(self.path),
                (attrs & ~FILE_ATTRIBUTE_HIDDEN)
            )
        
        except error as e:
            raise PermissionError(*e.args)

    def hidden(self) -> bool:
        from win32con import FILE_ATTRIBUTE_HIDDEN
        from win32file import GetFileAttributes

        attrs = GetFileAttributes(str(self.path))

        return bool(attrs & FILE_ATTRIBUTE_HIDDEN)

#========================================================

def script_dir(__file__:str) -> 'Path':
    """
    Get the directory of the current script
    """
    from os import path

    return Path(path.abspath(path=__file__)).parent()

def cwd() -> Path:
    """
    Get the Current Working Directory
    """
    from os import getcwd

    return Path(getcwd())

def mkdir(path:Path) -> None:
    """
    Make a Directory
    """
    from os import makedirs

    makedirs(
        name = str(path),
        exist_ok = True
    )

def link(src:Path, dst:Path) -> None:
    """
    Create a Symbolic Link
    """
    from os import link

    if dst.exists():
        dst.delete()

    mkdir(dst.parent())

    link(
        src = str(src),
        dst = str(dst)
    )

def temp() -> Path:
    from tempfile import gettempdir

    SERVER = Path('E:/__temp__/')

    OS = Path(gettempdir() + '/philh_myftp_biz/')

    if SERVER.exists():
        return SERVER
    else:
        mkdir(OS)
        return OS

def relscan(
    src: Path,
    dst: Path
) -> Generator[dict[Literal['src', 'dst'], Path]]:
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
    from .classOBJ import SharedBuffer
    from shutil import copytree
    from .process import thread

    buff = SharedBuffer()
    
    # Copytree dry run
    t = thread(

        func = copytree,

        src = str(src),
        dst = str(dst), 

        dirs_exist_ok = True,
        
        # Append paths to list instead of directly copying
        copy_function = lambda s, d, **_: buff.add({
            'src': Path(s), 
            'dst': Path(d)
        })

    )

    buff.stop_when = lambda: not t.running()

    yield from buff

#========================================================