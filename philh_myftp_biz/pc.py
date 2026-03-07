from typing import Literal, Self, Generator, TYPE_CHECKING, Any
from functools import cached_property

if TYPE_CHECKING:
    from .time import from_stamp
    from pathlib import PurePath as __PurePath

#========================================================

class PathPair:

    def __init__(self,
        src: Any,
        dst: Any
    ) -> None:
        self.src: Path = src
        self.dst: Path = dst

    def __setattr__(self,
        key: str, 
        value: Any
    ) -> None:

        if isinstance(value, Path):
            self.__dict__[key] = value
        else:
            self.__dict__[key] = Path(value)

class Path:
    """
    File/Folder
    """

    path: str
    
    def __init__(self,
        *input: 'str|__PurePath'
    ) -> None:
        from pathlib import Path as _Path
        from os import path as _path

        # ==================================

        if len(input) > 1:
            self.path = _path.join(*input)

        elif isinstance(input[0], Path):
            self.path = input[0].path

        elif hasattr(input[0], 'as_posix'):
            self.path = input[0].as_posix()

        else:
            self.path = input[0]

        # ==================================

        self.path = _Path(self.path).absolute().as_posix().replace('//', '/')

        # Append trailing slash
        if _path.isdir(self.path) and (self.path[-1] != '/'):
            self.path += '/'

        # ==================================

        # Declare 'pathlib.Path' attribute
        self._pure = _Path(self.path)

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
    
    @property
    def exists(self) -> bool:
        """Check if path exists"""
        return self._pure.exists()
    
    @cached_property
    def is_file(self) -> bool:
        """Check if path is a file"""
        return self._pure.is_file()
    
    @cached_property
    def is_dir(self) -> bool:
        """Check if path is a folder"""
        return self._pure.is_dir()

    def __str__(self):
        return self.path
    __repr__ = __str__

    @property
    def ctime(self):
        from .time import from_stamp
        from os import path

        stamp = path.getctime(self.path)

        return from_stamp(stamp)

    @cached_property
    def cd(self) -> '_cd':
        """
        Change the working directory to path
        
        If path is a file, then it will change to the file's parent directory
        """
        if self.is_file:
            return _cd(self.parent)
        else:
            return _cd(self)
    
    def is_child(self, parent:Path) -> bool:
        """
        Check if this path is a child or descendant of a parent directory
        """
        
        try:
            return self._pure.is_relative_to(str(parent))
        
        except ValueError:
            return False
        
    def is_parent(self, child:Path) -> bool:
        """
        Check if this path is a parent of ancestor of a path
        """
        return child.is_child(self)

    def related_to(self, path:Path) -> bool:
        """
        Check if this path is related to another
        
        ---
        Returns True is any of the following:
        - Is parent of
        - Is child of
        - Is same path
        """

        PARENT = self.is_parent(path)
        CHILD  = self.is_child(path)
        SAME   = (self == path)

        return any([PARENT, CHILD, SAME])
    
    def child(self, *name:str) -> Path:
        """
        Get child of path
        
        Note: Will raise TypeError if path is a file
        """

        if self.is_file:
            raise TypeError("Parent path cannot be a file")
        
        elif len(name) > 1:
            return Path(self.path + '/'.join(name))
        
        elif name[0].startswith('/'):
            return Path(self.path + name[0][1:])
            
        else:
            return Path(self.path + name[0])
    
    def __format__(self, spec:str) -> str:
        return f'{self.path:{spec}}'

    def __eq__(self,
        other: Path|Any
    ) -> bool:

        if isinstance(other, Path):
            testp = other.path

        elif hasattr(other, 'as_posix'):
            testp = other.as_posix()
        
        else:
            testp = str(other)
        
        return (self.path == testp)

    @property
    def size(self) -> int:
        """
        Get File Size

        Note: Will return TypeError is path is folder
        """
        from os import path

        if self.is_file:
            return path.getsize(self.path)
        else:
            raise TypeError("Cannot get size of a folder")

    @property
    def children(self) -> Generator[Path]:
        """
        Get children of current directory
        ```
        Curdir - |
                 | - Child
                 |
                 | - Child
        ```
        """

        if self.is_file:

            raise TypeError('Cannot get children of a file')

        else:

            for p in self._pure.iterdir():
                
                yield Path(p)

    @property
    def descendants(self) -> Generator[Path]:
        """
        Get descendants of current directory
        ```
        Curdir - |           | - Descendant
                 | - Child - |
                 |           |
                 |           | - Descendant
                 |           
                 | - Child - |
                             | - Descendant
        ```
        """

        for root, dirs, files in self._pure.walk():

            for item in (*dirs, *files):
            
                yield Path(root, item)

    @property
    def is_empty(self) -> bool:
        """
        Check if the current directory has any children
        """

        item: Path|None = next(self.children, None)

        return (item is None)

    @cached_property
    def parent(self) -> Path:
        """
        Get parent of current path
        """ 
        return Path(self._pure.parent.as_posix() + '/')

    def sibling(self, item:str) -> Path:
        """
        Get sibling of current path

        CurPath - |
                  |
        Sibling - |
                  |
        """
        return self.parent.child(item)
    
    @property
    def ext(self) -> str|None:
        """
        Get file extension of path
        """

        seg: str = self.seg()

        if '.' in seg:

            return seg[seg.rfind('.')+1:].lower()

    @cached_property
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
        if self.is_dir:
            from shutil import rmtree as delete
        
        # If path is a file
        else:
            from os import remove as delete

        # If the path exists
        if self.exists:

            # Update Access
            self.set_access.full()

            Log.VERB(f'Deleting: {self}')

            #            
            delete(self.path)

    def rename(self,
        dst: Path|str
    ) -> Path:
        """
        Change the name of the current path
        
        Returns updated path
        """
        from os import rename
        from .terminal import Log
        
        with self.parent.cd:

            dst = Path(dst)

            Log.VERB(f'Renaming:\nsrc={self}\ndst={dst}')

            if self != dst:

                if dst.exists:
                    dst.delete()
                
                rename(
                    src = self.path, 
                    dst = dst.path
                )

        return dst

    @cached_property
    def name(self) -> str:
        """
        Get the name of the current path

        Ex: 'C:/example.txt' -> 'example' 
        """

        name = self._pure.name

        # Check if file has ext
        if self.ext:
            # Return name without ext
            return name[:name.rfind('.')]

        else:
            # Return filename
            return name

    def seg(self,
        i: int = -1
    ) -> str:
        """
        Returns segment of path split by '/'
        (Ignores last slash)

        EXAMPLES:
        ```
        >>> Path('C:/example/test.log').seg(-1)
        'test.log'

        >>> Path('C:/example/').seg(-1)
        'example'
        ```
        """
        
        if self.path[-1] == '/':
            path = self.path[:-1]
        else:
            path = self.path
        
        return path.split(sep='/')[i]

    def copy(
        self,
        dst: 'Path'
    ) -> None:
        """
        Copy the path to another location
        """
        from shutil import copyfile
        from .terminal import Log

        files: list[PathPair] = []

        try:

            # If the source is a directory
            if self.is_dir:

                files = relscan(self, dst)

            # If the source is file and destination is folder 
            elif dst.is_dir:
                files = [PathPair(
                    src = self, 
                    dst = dst.child(self.seg())
                )]
                
            # If both the source and destination are files
            else:
                files = [PathPair(
                    src = self, 
                    dst = dst
                )]

            # Iter through source and destination pairs
            for file in files:

                Log.VERB(
                    f'Copying File\n'+ \
                    f'{file.src=}\n'+ \
                    f'{file.dst=}'
                )

                # Delete destination file
                file.dst.delete()

                # Create the parent folder of the destination file
                file.dst.parent.mkdir()

                # Copy the source file to the destination
                copyfile(
                    src = str(file.src),
                    dst = str(file.dst)
                )

        except Exception as e:

            # Delete destination paths
            for file in files:
                file.dst.delete()

            raise OSError(f'Failed to copy \n"{self}" \nto \n"{dst}" ') from e

    def move(self,
        dst: Self
    ) -> None:
        """
        Move the path to another location
        """
        self.copy(dst)
        self.delete()

    @property
    def in_use(self) -> bool:
        """
        Check if path is in use by another process
        """
        from os import rename

        if self.exists:
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

    def __setitem__(self,
        key: Any, 
        value: Any
    ) -> None:
        from .text import hex

        keyedpath: str = f'{self}:{hex.encode(key)}'

        try:

            # Store current mtime
            og_mtime = _mtime(self).get()

            with open(file=keyedpath, mode='w') as store:

                edata: str = hex.encode(value)

                store.write(edata)

            # Restore mtime
            _mtime(path=self).set(mtime=og_mtime)
        
        except OSError as e:

            raise OSError(f"Error setting var '{key}' at '{self.file}'") from e

    def __getitem__(self,
        key: Any
    ) -> None:
        from .text import hex

        keyedpath: str = f'{self}:{hex.encode(key)}'

        try:

            rvalue: str = open(file=keyedpath).read()
            
            return hex.decode(rvalue)
        
        except OSError:
            pass

    def mkdir(self) -> None:
        """
        Make this directory
        (will make parent directory if file)
        """
        from os import makedirs

        if self.is_file:

            folder = self.parent.path

        else:

            folder = self.path

        makedirs(
            name = folder,
            exist_ok = True
        )

    def link(self,
        link: Path
    ) -> None:
        """
        Create a Symbolic Link
        """
        from os import link as _link

        if link.exists:
            link.delete()

        link.parent.mkdir()

        _link(
            src = str(self),
            dst = str(link)
        )

    @cached_property
    def hash(self) -> str:
        """Calculate the SHA256 hash of a file."""
        from hashlib import sha256
        
        with self.open("rb") as f:
            
            return sha256(f.read()).hexdigest()

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

    @property
    def current(self):
        from .time import from_stamp
        from os import path

        mtime = path.getmtime( str(self.path) )

        return from_stamp(mtime)

    def stopwatch(self):
        from .time import Stopwatch

        SW = Stopwatch()

        SW.start_time = self.current
        
        return SW

class _set_access:

    def __init__(self, path:'Path'):
        self.path = path

    def __paths(self) -> Generator['Path']:

        yield self.path

        if self.path.is_dir:

            yield from self.path.descendants
    
    def readonly(self) -> None:
        from .terminal import Log
        from os import chmod

        Log.VERB(f'Updating Access [READ ONLY]: {self.path}')

        for path in self.__paths():

            chmod(str(path), 0o644)

    def full(self) -> None:
        from .process import RunHidden
        from .terminal import Log
        from os import chmod

        Log.VERB(f'Updating Access [FULL ACCESS]: {self.path}')

        if self.path.is_dir:

            RunHidden(['icacls', self.path, '/grant', 'Everyone:F', '/t', '/c', '/q'])

        else:
            chmod(str(self.path), 0o777)

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

    @property
    def hidden(self) -> bool:
        from win32con import FILE_ATTRIBUTE_HIDDEN
        from win32file import GetFileAttributes

        attrs = GetFileAttributes(str(self.path))

        return bool(attrs & FILE_ATTRIBUTE_HIDDEN)

#========================================================

def cwd() -> Path:
    """
    Get the Current Working Directory
    """
    from os import getcwd

    return Path(getcwd())

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
    from .classtools import SharedBuffer
    from shutil import copytree
    from .process import Thread

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

class WindowsService:

    def __init__(self, name:str):
        self.name = name

    def stop(self) -> None:
        from .process import RunHidden
        from .terminal import Log

        Log.VERB(f'Stopping Windows Service: {self.name}')

        RunHidden(['net', 'stop', self.name])

    def disable(self) -> None:
        from .process import RunHidden
        from .terminal import Log

        Log.VERB(f'Disabling Windows Service: {self.name}')

        RunHidden(['net', 'stop', self.name])

        RunHidden(['sc', 'config', self.name, 'start=disabled'])

#========================================================
# NAME

from socket import gethostname as __gethostname
NAME: str = __gethostname()

#=================================
# OS

from os import name as __name
OS: Literal['windows', 'unix'] 

match __name:

    case 'nt':
        OS = 'windows'
    
    case _:
        OS = 'unix'

#=================================
# TEMP DIR

from tempfile import gettempdir as __gettempdir

__temp_SERVER = Path('E:/__temp__/')

if __temp_SERVER.exists and (NAME == 'PC-1'):
    tempdir = __temp_SERVER
else:
    tempdir = Path(__gettempdir())

#========================================================
# SCRIPT DIR

from os import path as __path
from sys import argv as __argv

scriptdir = Path( __path.dirname(__path.abspath(__argv[0])) )

#========================================================
# CACHE DIR

pycache = scriptdir.child('/__pycache__/')

pycache.mkdir()

#========================================================