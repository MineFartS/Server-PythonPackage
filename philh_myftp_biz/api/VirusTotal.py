from functools import cached_property
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..pc import Path

class VirusTotal:

        def __init__(self):
            
            self.key = 'c063375af8061ad11694b15fb48327b3fd3c2a4f79cff8669f3de82143cc6562'

        @cached_property
        def client(self):
            from vt import Client

            return Client(self.key)

        def scan(self,
            file: 'Path'
        ):
            """Retrieve the analysis report for a file"""

            # TODO
        
            # Check for existing report first
            file_obj = self.client.get_object(f"/files/{file.hash}")

            return file_obj.last_analysis_stats, file_obj.permalink

