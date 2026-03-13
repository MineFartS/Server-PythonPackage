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

@dataclass
class FTP:

    host: str
    username: str
    password: str
    timeout: int = None
    port: int = 22

    @cached_property
    def _client(self):
        from ftplib import FTP as __FTP

        return __FTP(
            host = self.host,
            port = self.port,
            user = self.username,
            passwd = self.password,
            timeout = self.timeout
        )
    
    def cd(self, path:str) -> None:
        self._client.cwd(path)

    @cached_property
    def children(self) -> Generator[FTPPath]:
        
        for path in self._client.nlst():

            yield FTPPath(self, path)

