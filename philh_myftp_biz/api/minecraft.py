from functools import cached_property
from typing import Literal

class ModrinthMod:

    def __init__(self,
        name: str,
        loader: Literal['fabric', 'forge'] = 'fabric'
    ) -> None:
        from ..web import get

        self.loader = loader

        request = get(
            url = f'https://api.modrinth.com/v2/project/{name}/version',
            params = {
                'loaders': [loader]
            }
        )

        for item in request.json():

            if item['version_type'] == 'release':

                self._data = item

                break

    @cached_property
    def url(self) -> str:
        return self._data['files'][0]['url']
