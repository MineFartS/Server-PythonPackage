from typing import Literal, TYPE_CHECKING
from functools import cached_property
from ..functools import singleton
from dataclasses import dataclass

from .url import URL # pyright: ignore[reportUnusedImport]
from .session import Session, Adapter, RetryStrat # pyright: ignore[reportUnusedImport]

if TYPE_CHECKING:
    from ..pc import Path

@singleton
class IP:

    @cached_property
    def LAN(self) -> str:
        from socket import gethostname, gethostbyname

        return gethostbyname(gethostname())
    
    @cached_property
    def WAN(self) -> str:
        return URL('https://api.ipify.org').text
    
    @cached_property
    def ROUTER(self) -> str:
        from netifaces import gateways, AF_INET

        return gateways().get('default', {}).get(AF_INET)[0]

class Port:
    """Details of a port on a network device"""

    def __init__(self,
        port: int,
        host: str = '127.0.0.1'
    ) -> None:
        
        self.port: int = port

        self.addr: tuple[str, int] = (host, port)

    @property
    def listening(self) -> bool:
        """Check if Port is listening/in use"""

        from socket import error, SHUT_RDWR
        from quicksocketpy import socket

        sock = socket()

        try:
            
            sock.connect(self.addr)
            sock.shutdown(SHUT_RDWR)
            
            sock.close()

            return True

        except error:

            sock.close()
            return False

    def __int__(self) -> int:
        return self.port
    
    def __repr__(self) -> str:
        return f"Port({self.port})"

@dataclass
class FirewallException:

    name: str

    def __repr__(self) -> str:
        return f'FirewallException({self.name})'

    @property
    def exists(self) -> bool:
        """Check if this exception exists in Windows Defender"""
        from ..process import RunHidden

        p = RunHidden(
            'netsh', 'advfirewall', 'firewall', 
            'show', 'rule', f'name={self.name}'
        )

        return ("No rules match the specified criteria." not in p.output())
    
    def delete(self) -> None:
        """Remove this exception from Windows Defender"""
        from ..process import RunHidden

        RunHidden(
            'netsh', 'advfirewall', 'firewall',
            'delete',
            'rule', f'name={self.name}'
        )

    def set(self,
        i: 'int | Path',
        dir: Literal['in', 'out'] = 'in'
    ) -> None:
        """
        Add this exception to Windows Defender

        (Deletes & Readds if it already exists)
        """
        from philh_myftp_biz.pc import Path
        from ..process import RunHidden

        if self.exists:
            self.delete()
        
        args = [
            'netsh', 'advfirewall', 'firewall',
            'add', 'rule', f'name={self.name}',
            f'dir={dir}',
            'action=allow',
            'protocol=TCP'
        ]

        if isinstance(i, int):
            args += [f'localport={i}']
        elif isinstance(i, Path):
            args += [f'program={i.wpath}']

        RunHidden(*args)

