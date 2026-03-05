from functools import cached_property

class VirusTotal:

        def __init__(self):
            
            self.key = 'c063375af8061ad11694b15fb48327b3fd3c2a4f79cff8669f3de82143cc6562'

        @cached_property
        def client(self):
            from vt import Client

            return Client(self.key)

        def scan(self,
            #file: Path
        ):
            """
            Retrieve the analysis report for a file
            """

            # TODO
            
            """
            self.client
    
                try:
        
                    # Check for existing report first
                    file_obj = client.get_object(f"/files/{file_hash}")
        
                    return file_obj.last_analysis_stats, file_obj.permalink
    
                except vt.APIError as e:
                    if e.code == 'NotFoundError':
                        return None, None
                    else:
                        print(f"Error retrieving report: {e}")
                        return None, None
            
            get(
                url = 'https://www.virustotal.com/api/v3/files',
                headers = {'x-apikey': self.key},
                params = {}
            )"""
