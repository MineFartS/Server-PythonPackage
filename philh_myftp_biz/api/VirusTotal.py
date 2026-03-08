from functools import cached_property
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

        self.results: dict = VTobj.last_analysis_results
    
    @cached_property
    def warnings(self) -> list[dict]:

        _warnings = []

        for data in self.results.values():

            if data['result'] != None:
            
                _warnings += {data}

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

class VirusTotal:

        def __init__(self):
            
            self.key = 'c063375af8061ad11694b15fb48327b3fd3c2a4f79cff8669f3de82143cc6562'

        @cached_property
        def client(self):
            from vt import Client

            return Client(self.key)

        def scan(self,
            file: 'Path'
        ) -> VirusReport:
            """Retrieve the analysis report for a file"""

            # TODO
        
            # Check for existing report first
            obj = self.client.get_object(f"/files/{file.hash}")

            return VirusReport(file, obj)

            #return file_obj.last_analysis_stats, file_obj.permalink
        
            # with open("path/to/file.exe", "rb") as f:
            #     analysis = client.scan_file(f)
            #     print(analysis)

