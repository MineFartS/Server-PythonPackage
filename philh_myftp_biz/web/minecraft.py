from functools import cached_property, cache
from ..classtools import singleton
from dataclasses import dataclass
from typing import Literal, Any

@singleton
class Mojang:

    @staticmethod
    @cache
    def _data() -> dict[str, Any]:
        from ..web import URL

        url = URL('https://piston-meta.mojang.com/mc/game/version_manifest_v2.json')
        
        return url.get().json()

    @property
    def java_latest(self) -> str:
        return self._data()['latest']['release']

@dataclass
class ModrinthMod:

    name: str
    loader: Literal['fabric', 'forge'] = 'fabric'
    
    @property
    def version(self) -> str:
        # TODO Add more version options
        return Mojang.java_latest

    @cached_property
    def _data(self) -> dict[str, Any] | None:
        from ..web import URL

        url = URL(f'https://api.modrinth.com/v2/project/{self.name}/version')

        for item in url.get().json():

            if self.version in item['game_versions']:

                return item

    @property
    def url(self) -> None | str:
        if self._data:
            return self._data['files'][0]['url']

@singleton
class FabricMC:

    @cached_property
    def serverURL(self) -> str:
        """URL of Server jarfile"""
        return f'https://meta.fabricmc.net/v2/versions/loader/{self.gameV}/{self.loaderV}/{self.installerV}/server/jar'

    @cached_property
    def gameV(self) -> str: # pyright: ignore[reportReturnType]
        """Game Version"""
        from ..web import URL

        request = URL('https://meta.fabricmc.net/v2/versions/game').json()

        for item in request:

            if item['stable']:

                return item['version']
            
    @cached_property
    def loaderV(self) -> str: # pyright: ignore[reportReturnType]
        """Loader Version"""
        from ..web import URL

        request = URL(f'https://meta.fabricmc.net/v1/versions/loader/{self.gameV}').json()

        for item in request:

            if item['loader']['stable']:

                return item['loader']['version']

    @cached_property
    def installerV(self) -> str: # pyright: ignore[reportReturnType]
        """Installer Version"""
        from ..web import URL

        request = URL(f'https://meta.fabricmc.net/v2/versions/installer').json()

        for item in request:

            if item['stable']:

                return item['version']
