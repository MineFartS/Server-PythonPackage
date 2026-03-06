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

class FabricMC:

    @cached_property
    def serverURL(self) -> str:
        """URL of Server jarfile"""
        return f'https://meta.fabricmc.net/v2/versions/loader/{self.gameV}/{self.loaderV}/{self.installerV}/server/jar'

    @cached_property
    def gameV(self) -> str: # pyright: ignore[reportReturnType]
        """Game Version"""
        from ..web import get

        request = get('https://meta.fabricmc.net/v2/versions/game')

        for item in request.json():

            if item['stable']:

                return item['version']
            
    @cached_property
    def loaderV(self) -> str: # pyright: ignore[reportReturnType]
        """Loader Version"""
        from ..web import get

        request = get(f'https://meta.fabricmc.net/v1/versions/loader/{self.gameV}')

        for item in request.json():

            if item['loader']['stable']:

                return item['loader']['version']

    @cached_property
    def installerV(self) -> str: # pyright: ignore[reportReturnType]
        """Installer Version"""
        from ..web import get

        request = get(f'https://meta.fabricmc.net/v2/versions/installer')

        for item in request.json():

            if item['stable']:

                return item['version']
