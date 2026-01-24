from typing import Literal, Self, Generator, TYPE_CHECKING

if TYPE_CHECKING:
    from .time import from_stamp

from socket import gethostname as NAME

#========================================================

from os import name as __name
OS: Literal['windows', 'unix'] = {
    True: 'windows',
    False: 'unix'
} [__name == 'nt']

#========================================================

class Path:
    """
    File/Folder
    """

    def __init__(self, *input):
        from pathlib import Path as libPath, PurePath
        from os import path

        # ==================================

        if len(input) > 1:
            joined: str = path.join(*input)
            self.path = joined.replace('\\', '/')

        elif isinstance(input[0], Path):
            self.path = input[0].path

        elif isinstance(input[0], str):
            self.path = libPath(input[0]).absolute().as_posix()

            if input[0][-1] == '/':                
                self.path += '/'

        elif isinstance(input[0], PurePath):
            self.path = input[0].as_posix()

        elif isinstance(input[0], libPath):
            self.path = input[0].as_posix()

        # ==================================

        # Declare path string
        self.path: str = self.path.replace('\\', '/').replace('//', '/')
        """File Path with forward slashes"""

        # Declare 'pathlib.Path' attribute
        self.__Path = libPath(self.path)

        # Link 'exists', 'isfile', & 'isdir' functions from 'self.__Path'
        self.exists = self.__Path.exists
        """Check if path exists"""

        self.isfile = self.__Path.is_file
        """Check if path is a file"""
        
        self.isdir = self.__Path.is_dir
        """Check if path is a folder"""

        # Declare 'set_access'
        self.set_access = _set_access(self)
        """Filesystem Access"""

        # Declare 'mtime'
        self.mtime = _mtime(self)
        """Modified Time"""

        # Declare 'visibility'
        self.visibility = _visibility(self)
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
    
    def resolute(self) -> Self:
        """
        Get path with Symbolic Links Resolved
        """
        return Path(self.__Path.resolve(True))
    
    def child(self, *name:str) -> Self:
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
    
    def __format__(self, spec):
        return f'{self.path:{spec}}'

    def __eq__(self, other) -> bool:

        if isinstance(other, Path):
            return (self.path == other.path)
        else:
            return False

    def islink(self) -> bool:
        """
        Check if path is Symbolic Link or Directory Junction
        """

        return (self.__Path.is_symlink() or self.__Path.is_junction())

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

    def children(self) -> Generator[Self]:
        """
        Get children of current directory

        Curdir - |
                 | - Child
                 |
                 | - Child
        """
        for p in self.__Path.iterdir():
            yield Path(p)

    def descendants(self) -> Generator[Self]:
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
        for root, dirs, files in self.__Path.walk():
            for item in (dirs + files):
                yield Path(root, item)

    def isempty(self):
        
        if self.isfile():
            raise TypeError('Cannot get children of a file')
        
        else:
            for p in self.children():
                return False
            return True

    def parent(self) -> Self:
        """
        Get parent of current path
        """ 
        return Path(self.__Path.parent.as_posix() + '/')

    def var(self, name:str, default=None) -> '_var':
        """
        Get Variable Object for storing custom metadata
        """
        return _var(self, name, default)
    
    def sibling(self, item) -> Self:
        """
        Get sibling of current path

        CurPath - |
                  |
        Sibling - |
                  |
        """
        return self.parent().child(item)
    
    def ext(self) -> str:
        """
        Get file extension of path
        """
        from os import path

        ext = path.splitext(self.path)[1][1:]
        if len(ext) > 0:
            return ext.lower()

    def type(self) -> None | str:
        """
        Get mime type of path
        """
        from .db import MimeType

        return MimeType.Path(self)

    def delete(self) -> None:
        """
        Delete the current path

        Uses the 'send2trash' package.
        Will use 'os.remove' if send2trash raises an OSError.
        """
        from send2trash import send2trash
        from shutil import rmtree
        from .terminal import Log
        from os import remove

        if self.exists():
            
            self.set_access.full()

            try:

                Log.VERB(f'Recycling: {str(self)=}')
                
                send2trash(self.path)

            except OSError:

                Log.VERB(f'Deleting: {str(self)=}', exc_info=True)

                if self.isdir():
                    rmtree(self.path)
                else:
                    remove(self.path)

    def rename(self,
        dst,
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

        name = self.__Path.name

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
            path = self.path[:-1]
        else:
            path = self.path
        
        return path.split('/') [i]

    def copy(
        self,
        dst: 'Path'
    ) -> 'Path':
        """
        Copy the path to another location
        """
        from shutil import copyfile, copytree
        from .terminal import Log

        Log.VERB(f'Initializing Copier: {str(self)=} | {str(dst)=}')

        pairs: list[list[Path, Path]] = []

        # If the source is a file
        if self.isfile():

            # If the destination is a folder
            if dst.isdir():
                pairs += [[self, dst.child(self.seg())]]
            
            # If the destination is a file
            else:
                pairs += [[self, dst]]

        # If the source is a folder
        else:

            copytree(

                src = str(self),
                dst = str(dst), 

                dirs_exist_ok = True,
                
                # Append paths to list instead of directly copying
                copy_function = lambda s, d, **_: \
                    pairs.append([Path(s), Path(d)])

            )

        try:

            # Iter through source and destination pairs
            for src, dst in pairs:

                Log.VERB(f'Copying File: {str(src)=} | {str(dst)=}')

                copyfile(
                    src = str(src),
                    dst = str(dst)
                )

            Log.VERB(f'Copy Completed: {str(src)=} | {str(dst)=}')

        except Exception as e:

            Log.VERB(f'Copy Failed: {str(src)=} | {str(dst)=}')

            # Iter through source and destination pairs
            for src, dst in pairs:

                dst.delete()

            raise e

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

    def open(self, mode='r'):
        """
        Open the current file

        Works the same as: open(self.Path)
        """
        return open(self.path, mode)

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

    def stopwatch(self):
        from .time import Stopwatch, from_stamp
        from os import path

        SW = Stopwatch()

        mtime = path.getmtime( str(self.path) )

        SW.start_time = from_stamp(mtime)
        
        return SW

class _var:

    def __init__(self,
        file: Path,
        title: str,
        default = None
    ):
        from .text import hex

        self.file = file
        self.title = title
        self.default = default

        self.path = file.path + ':' + hex.encode(title)

        file.set_access.full()

    def read(self):
        from .text import hex

        try:
            value = open(self.path).read()
            return hex.decode(value)
        except OSError:
            return self.default
        
    def save(self, value):
        from .text import hex
        
        try:

            m = _mtime(self.file).get()

            open(self.path, 'w').write(
                hex.encode(value)
            )

            _mtime(self.file).set(m)
        
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

def script_dir(__file__) -> 'Path':
    """
    Get the directory of the current script
    """
    from os import path

    return Path(path.abspath(__file__)).parent()

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

def relscan(
    src: Path,
    dst: Path
) -> list[dict[Literal['src', 'dst'], Path]]:
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
    from os import listdir

    items = []

    def scanner(src_:Path, dst_:Path):
        for item in listdir(src.path):

            s = src_.child(item)
            d = dst_.child(item)

            if s.isfile():
                items.append({
                    'src': s,
                    'dst': d
                })

            elif s.isdir():
                scanner(s, d)
            
    scanner(src, dst)
    
    return items

#========================================================