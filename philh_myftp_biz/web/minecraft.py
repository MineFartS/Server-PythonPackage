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
        
        return url.json # pyright: ignore[reportReturnType]

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

        for item in url.json:

            if self.version in item['game_versions']:

                return item

    @property
    def url(self) -> None | str:
        if self._data:
            return self._data['files'][0]['url']

@singleton
class FabricMC:

    _server_jar: None|str = None

    @cached_property
    def server_jar(self) -> str:
        from .driver import Driver

        if self._server_jar is None:
            with Driver() as d:
                d.open('https://fabricmc.net/use/server/')
                self._server_jar = d.element('xpath', '/html/body/main/div/article/div/div[1]/main/div[1]/div[4]/a')[0].get_attribute('href')
        
        return self._server_jar # pyright: ignore[reportReturnType]

