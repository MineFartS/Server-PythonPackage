from functools import cached_property
from dataclasses import dataclass
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from paramiko.channel import ChannelFile, ChannelStderrFile

@dataclass
class SSHResponse:

    stdout: 'ChannelFile'
    stderr: 'ChannelStderrFile'

    @cached_property
    def output(self) -> str:
        return self.stdout.read().decode()

    @cached_property
    def error(self) -> str:
        return self.stderr.read().decode()

@dataclass
class SSH:

    host: str
    username: str
    password: str
    timeout: int = None
    port: int = 22

    @cached_property
    def _client(self):
        from paramiko import SSHClient, AutoAddPolicy
        from ..terminal import Catcher

        Catcher.TimeoutError.handler = ConnectionAbortedError
        Catcher.TimeoutError.enable()

        client = SSHClient()

        client.set_missing_host_key_policy(policy=AutoAddPolicy())

        client.connect(
            hostname = self.host, 
            port = self.port, 
            username = self.username, 
            password = self.password, 
            timeout = self.timeout
        )

        return client
    
    def close(self) -> None:
        from ..terminal import Catcher

        Catcher.TimeoutError.handler = None
        Catcher.TimeoutError.disable()

        self._client.close()


        del self._client

    def run(self, command:str) -> SSHResponse:
        """Send a command to the remote computer"""

        # Execute a command
        stdout, stderr = self._client.exec_command(command)[1:]

        return SSHResponse(stdout, stderr)
