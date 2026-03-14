from functools import cached_property
from dataclasses import dataclass
from typing import TYPE_CHECKING, Generator

if TYPE_CHECKING:
    from ..pc import Path

@dataclass
class FTPPath:

    ftp: FTP
    path: str

    def __str__(self) -> str:
        return self.path

    __repr__ = __str__

    def download(self,
        local: 'Path'
    ) -> None:

        # Open the local file in write-binary mode
        with local.open('wb') as stream:

            # Download the file using retrbinary
            self.ftp._client.retrbinary(
                f"RETR {self.path}",
                stream.write
            )

    @cached_property
    def cd(self) -> _cd:
        return _cd(self.ftp, self)

    @property
    def is_dir(self) -> bool:
        from ftplib import error_perm

        try:
            self.cd.open()
            self.cd.back()
            return True
        except error_perm:
            return False
    
    @property
    def is_file(self) -> bool:
        return (not self.is_dir)
    
    def child(self, name:str) -> "FTPPath":
        
        if self.is_file:
            raise TypeError("Parent path cannot be a file")

        return FTPPath(self.path.rstrip('/') + '/' + name)

    @cached_property
    def children(self) -> Generator[FTPPath]:

        with self.cd:
        
            for name in self.ftp._client.nlst():

                yield FTPPath(
                    ftp = self.ftp,
                    path = (self.path.rstrip('/') + '/' + name)
                )

    @cached_property
    def descendants(self) -> Generator[FTPPath]:

        def _scan(path:FTPPath):
    
            for _path in path.children:

                yield _path
            
                if _path.is_dir:
                    yield from _scan(_path)

        yield from _scan(self)

    def seg(self,
        i: int = -1
    ) -> str:
        
        if self.path[-1] == '/':
            path = self.path[:-1]
        else:
            path = self.path
        
        return path.split(sep='/')[i]

    @property
    def ext(self) -> str|None:

        seg: str = self.seg()

        if '.' in seg:

            return seg[seg.rfind('.')+1:].lower()
        
    @cached_property
    def name(self) -> str:

        name = self.seg()

        # Check if file has ext
        if self.ext:
            # Return name without ext
            return name[:name.rfind('.')]

        else:
            # Return filename
            return name

    @property
    def size(self) -> int:

        if self.is_file:
            return self.ftp._client.size(self.path) # pyright: ignore[reportReturnType]
        else:
            raise TypeError("Cannot get size of a folder")

@dataclass
class FTP:

    host: str
    username: str
    password: str
    timeout: int = None
    port: int = 21

    @cached_property
    def _client(self):
        from ftplib import FTP as __FTP

        ftp = __FTP(
            timeout = self.timeout
        )

        ftp.connect(
            host = self.host, 
            port = self.port
        )

        ftp.login(
            user = self.username, 
            passwd = self.password
        )

        ftp.encoding = 'latin-1'

        return ftp
    
    def cd(self,
        path: FTPPath
    ) -> None:
        self._client.cwd(str(path))

    @property
    def cwd(self) -> FTPPath:
        return FTPPath(self, self._client.pwd())

    def Path(self, path:str) -> FTPPath:
        return FTPPath(self, path)

@dataclass
class _cd:

    ftp: FTP
    path: FTPPath

    __via_with = False
    
    def __enter__(self) -> None:
        self.__via_with = True
        self.open()

    def __exit__(self, *_) -> None:
        if self.__via_with:
            self.back()

    def open(self) -> None:
        """Change CWD to the given path"""

        self._back = self.ftp.cwd

        self.ftp.cd(self.path)

    def back(self) -> None:
        """Change CWD to the previous path"""
        self.ftp.cd(self._back)
