from functools import cached_property
from ..classtools import singleton
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vt.object import Object as VTobj
    from ..pc import Path

class VirusReport:

    def __init__(self,
        file: Path,
        VTobj: 'VTobj'
    ) -> None:

        self.file = file

        self._VTobj = VTobj

        self.results: dict[str, dict] = VTobj.last_analysis_results

    @cached_property
    def url(self) -> str:
        return f"https://www.virustotal.com/gui/file/{self._VTobj.id}"
    
    @cached_property
    def warnings(self) -> list[dict]:

        _warnings = []

        for data in self.results.values():

            if data['result'] != None:
            
                _warnings += {data} # pyright: ignore[reportUnhashable]

        return _warnings

    @cached_property
    def score(self):
        """
        Safety Score
        
        ```
        0: Unsafe
        ...
        1: Safe
        ```
        """

        total = len(self.results)
        
        undetected = (total - len(self.warnings))

        return (undetected / total)

@singleton
class VirusTotal:

    key = 'c063375af8061ad11694b15fb48327b3fd3c2a4f79cff8669f3de82143cc6562'

    @property
    def client(self):
        from vt import Client

        return Client(self.key)

    def _upload(self,
        file: 'Path',
        wait: bool = True
    ) -> VTobj:
        
        with file.open("rb") as f:

            with self.client as client:
            
                obj = client.scan_file(f, wait)

            return obj
        
    def _check(self,
        file: 'Path'
    ) -> VTobj | None:
        from vt.error import APIError
    
        try: # Check for existing report first

            return self.client.get_object(f"/files/{file.hash}")

        except APIError as e:

            if e.args[0] != 'NotFoundError':
                
                raise e

    def scan(self,
        file: 'Path'
    ) -> VirusReport:
        """Retrieve the analysis report for a file"""
    
        obj = self._check(file)

        if obj:

            return VirusReport(file, obj)
        
        else:

            self._upload(file)

            obj = self._check(file)

            return VirusReport(file, obj)
