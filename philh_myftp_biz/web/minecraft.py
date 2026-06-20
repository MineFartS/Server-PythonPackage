from functools import cached_property, cache
from ..classtools import singleton
from dataclasses import dataclass
from typing import Literal, Any
from . import URL

@singleton
class Mojang:

    @staticmethod
    @cache
    def _data() -> dict[str, Any]:
        from ..web import URL

        url = URL('https://piston-meta.mojang.com/mc/game/version_manifest_v2.json')
        
        return url.json # pyright: ignore[reportReturnType]

    @property
    def latest(self) -> URL:
        return URL(self._data()['latest']['release'])
    
    _selected = None

    @property
    def selected(self):
        if self._selected is None:
            self._selected = self.latest

        return self._selected
    
    @selected.setter
    def selected(self, value:str):
        self._selected = value

@dataclass
class ModrinthMod:

    name: str
    loader: Literal['fabric', 'forge'] = 'fabric'

    @cached_property
    def url(self) -> URL | None:
        from ..json import List

        url = URL(f'https://api.modrinth.com/v2/project/{self.name}/version')

        items = List(url.json)

        items.filter(
            lambda i: (Mojang.selected in i['game_versions'][0])
        )

        items.filter(
            lambda i: i['loaders'][0] == self.loader
        )

        if len(items) > 0:
            return URL(items[0]['files'][0]['url'])

@singleton
class FabricMC:

    @cached_property
    def server_jar(self) -> URL:
        from selenium.webdriver.support.ui import Select
        from .driver import Driver

        with Driver() as d:

            d.open('https://fabricmc.net/use/server/')

            Select(d.element('id', 'minecraft-version')[0]) \
                .select_by_visible_text(Mojang.selected)

            url: str = d.element(
                'xpath', 
                '/html/body/main/div/article/div/div[1]/main/div[1]/div[4]/a'
            )[0].get_attribute('href')

            return URL(url)
