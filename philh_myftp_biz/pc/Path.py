from typing import Literal, Generator, TYPE_CHECKING, Any
from functools import cached_property
from dataclasses import dataclass
from .. import file

if TYPE_CHECKING:
    from ..time import from_stamp

#========================================================

class Path:

    path: str
    
    @staticmethod
    def _parse(path:Any) -> str:
        from os import path as _path

        if isinstance(path, Path):
            fpath = path.path
        elif hasattr(path, 'as_posix'):
            fpath = path.as_posix()
        else:
            fpath = str(path)

        fpath: str = fpath.replace('\\', '/').replace('//', '/')

        if _path.isdir(fpath) and (fpath[-1] != '/'):
            fpath += '/'

        return fpath

    def __init__(self, path:Any) -> None:
        from pathlib import Path as PurePath

        self.path = self._parse(path)
        self.wpath: str = self.path.replace('/', '\\')

        self._pure = PurePath(self.path)

        self.set_access = _set_access(self)
        self.mtime = _mtime(self)
        self.visibility = _visibility(self)

        self.name = self._pure.stem
        self.ext = self._pure.suffix.strip('.')

    @property
    def exists(self) -> bool:
        return self._pure.exists()
    
    @cached_property
    def is_file(self) -> bool:
        return self._pure.is_file()
    
    @cached_property
    def is_dir(self) -> bool:
        return self.path[-1]=='/' or self._pure.is_dir()

    __str__ = lambda s: s.path
    __repr__ = __str__

    @property
    def ctime(self):
        from ..time import from_stamp
        from os import path

        stamp = path.getctime(self.path)

        return from_stamp(stamp)

    @cached_property
    def cd(self) -> '_cd':
        """Change the working directory to path"""
        if self.is_file:
            return _cd(self.parent)
        else:
            return _cd(self)
    
    def is_child(self, parent:Path) -> bool:
        """Check if this path is a child or descendant of a parent directory"""
        try:
            return self._pure.is_relative_to(str(parent))
        except ValueError:
            return False
        
    def is_parent(self, child:Path) -> bool:
        """Check if this path is a parent or ancestor of a path"""
        return child.is_child(self)

    def related_to(self, path:Path) -> bool:
        """Check if this path is related to another"""
        return any([
            self.is_parent(path),
            self.is_child(path),
            (self == path)
        ])
    
    def child(self,
        name: str
    ) -> Path:
        if self.is_file:
            raise TypeError("Parent path cannot be a file")

        return Path(self.path + name)
    
    def __format__(self, spec:str) -> str:
        return f'{self.path:{spec}}'

    def __eq__(self, other:Any) -> bool:
        return (self.path == self._parse(other))

    @property
    def size(self) -> None|int:
        """Get File Size"""
        from os import path

        if self.is_file:
            return path.getsize(self.path)
        
    @property
    def fsize(self) -> str:
        from ..db import Size

        return Size.from_bytes(self.size, ndigits=2)

    @property
    def children(self) -> Generator[Path]:
        if self.is_file:
            raise TypeError('Cannot get children of a file')
        
        return (Path(p) for p in self._pure.iterdir())

    @property
    def descendants(self) -> Generator[Path]:
        if self.is_file:
            raise TypeError('Cannot get children of a file')
        
        yield from (Path(i) for i in self._pure.rglob('*'))

    @property
    def is_empty(self) -> bool:
        """Check if the current directory has any children"""
        return (next(self.children, None) is None)

    @cached_property
    def parent(self) -> Path:
        return Path(self._pure.parent)

    def sibling(self, item:str) -> Path:
        return self.parent.child(item)
    
    @cached_property
    def type(self) -> None | str:
        from ..db import MimeType
        return MimeType.Path(self)

    def delete(self) -> None:
        from ..terminal import Log

        if self.is_dir:
            from shutil import rmtree as delete
        else:
            from os import remove as delete

        if self.exists:

            self.set_access.full()

            Log.VERB(f'Deleting: {self}')

            delete(self.path)

    def rename(self, dst:Any) -> Path:
        from ..terminal import Log
        from os import rename
        
        with self.parent.cd:

            dst = Path(dst)

            Log.VERB(f'Renaming:\nsrc={self}\ndst={dst}')

            if self != dst:

                dst.delete()

                rename(
                    src = self.path, 
                    dst = dst.path
                )

        return dst

    def seg(self,
        i: int = -1
    ) -> str:
        """
        Returns segment of path split by '/'
        (Ignores last slash)
        """
        
        return self.path.trim('/').split(sep='/')[i]

    def copy(self, dst:Path) -> None:
        from ..terminal import Log, ProgressBar
        from . import relscan

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

            pbar = ProgressBar(
                total = sum(f.src.size for f in files), 
                label = "Copying Files",
                mode  = 'FSTREAM',
                verbose = True
            )

            # Iter through source and destination pairs
            for file in files:

                Log.VERB(
                    f'Copying File\n'+ \
                    f'{file.src=}\n'+ \
                    f'{file.dst=}'
                )

                # Create the parent folder of the destination file
                file.dst.parent.mkdir()

                file.src.set_access.full()
                file.dst.set_access.full()

                srcIO = file.src.open('rb')
                dstIO = file.dst.open('wb')

                for chunk in iter(lambda: srcIO.read(8192), b""):
                    pbar.step(chunk)
                    dstIO.write(chunk)

                srcIO.close()
                dstIO.close()

            pbar.stop()

        except Exception as e:
            (f.dst.delete() for f in files)
            raise e

    def move(self, dst:Any) -> None:
        self.copy(dst)
        self.delete()

    @property
    def in_use(self) -> bool:
        from os import rename

        if not self.exists:
            return False
        
        try:
            rename(self.path, self.path)
            return False
        except PermissionError:
            return True

    def open(self,
        mode: Literal['r', 'w', 'a', 'rb', 'wb', '+'] = 'r'
    ):

        if 'w' in mode:
            self.parent.mkdir()
        
        return open(
            file = self.path, 
            mode = mode,
            encoding = None if ('b' in mode) else 'utf-8'
        )

    @property
    def siblings(self):
        return [c for c in self.parent.children if c!=self]

    def __setitem__(self,
        key: Any, 
        value: Any
    ) -> None:
        from ..text import hex

        og_mtime = self.mtime.get()

        with open(f'{self}:{hex.encode(key)}', 'w') as store:
            store.write(hex.encode(value))

        _mtime(path=self).set(mtime=og_mtime)

    def __getitem__(self,
        key: Any
    ) -> None:
        from ..text import hex

        try:
            with open(f'{self}:{hex.encode(key)}') as store:                
                return hex.decode(store.read())        
        except OSError:
            pass

    def mkdir(self) -> None:
        from os import makedirs
        makedirs(
            name = (self.parent if self.is_file else self).path,
            exist_ok = True
        )

    def link(self, link:Path) -> None:
        from os import link as _link

        if link.exists:
            link.delete()

        link.parent.mkdir()

        _link(str(self), str(link))

    @property
    def hash(self) -> None | str:
        from hashlib import sha256

        if not self.exists or self.is_dir:
            return

        try:
        
            hasher = sha256()
            
            with self.open("rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)
            
            return hasher.hexdigest()
        
        except OSError:
            pass
    
    #========================================================
    # File Parsers

    XML : file.XML
    PKL : file.PKL
    JSON: file.JSON
    INI : file.INI
    YAML: file.YAML
    TXT : file.TXT
    ZIP : file.ZIP
    CSV : file.CSV
    TOML: file.TOML

    def __getattr__(self, name:str):
        from typing import get_type_hints

        clazz: Any = get_type_hints(self.__class__).get(name)

        if clazz:
            return clazz(self)
        else:
            return super().__getattribute__(name)
        
    #========================================================

@dataclass
class PathPair:

    src: Path|Any
    dst: Path|Any

    def __setattr__(self, key:str, value:Any) -> None:
        self.__dict__[key] = Path(value)

class _cd:

    __via_with = False
    
    def __enter__(self) -> None:
        self.__via_with = True

    def __exit__(self, *_) -> None:
        if self.__via_with:
            self.back()

    def __init__(self, path:Path) -> None:
        self._target = str(path)
        self.open()

    def open(self) -> None:
        from os import getcwd, chdir

        self._back = getcwd()

        chdir(self._target)

    __call__ = open

    def back(self) -> None:
        from os import chdir
        chdir(self._back)

@dataclass
class _mtime:

    path: Path

    def set(self,
        mtime: int | 'from_stamp' = None
    ) -> None:
        from ..time import from_stamp
        from ..time import now
        from os import utime


        if mtime:
            utime(
                str(self.path), 
                (int(mtime), int(mtime))
            )
        else:
            nowt = now().unix
            utime(str(self.path), (nowt, nowt))

    @property
    def current(self):
        from ..time import from_stamp
        from os import path

        return from_stamp(
            path.getmtime( str(self.path) )
        )

    def stopwatch(self):
        from ..time import Stopwatch

        SW = Stopwatch()

        SW.start_time = self.current
        
        return SW

@dataclass
class _set_access:

    path: Path

    def __paths(self) -> Generator['Path']:

        yield self.path

        if self.path.is_dir:
            yield from self.path.descendants
    
    def readonly(self) -> None:
        from ..terminal import Log
        from os import chmod

        if self.path.in_use:
            Log.VERB(f'Failed to Update Access: {self.path}')
        
        elif self.path.exists:
            for path in self.__paths():
                chmod(str(path), 0o644)

    def full(self) -> None:
        from ..process import RunHidden
        from ..terminal import Log
        from os import chmod

        if self.path.is_dir:
            RunHidden(['icacls', self.path, '/grant', 'Everyone:F', '/t', '/c', '/q'])

        elif self.path.in_use:
            Log.VERB(f'Failed to Update Access: {self.path}')

        elif self.path.exists:
            chmod(str(self.path), 0o777)

@dataclass
class _visibility:

    path: Path

    def hide(self) -> None:
        from win32con import FILE_ATTRIBUTE_HIDDEN
        from win32file import GetFileAttributes
        from win32api import SetFileAttributes
        from pywintypes import error

        if self.hidden:
            return

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

        if not self.hidden:
            return

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
