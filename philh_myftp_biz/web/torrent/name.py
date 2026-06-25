from functools import cached_property
from typing import Literal

qualities: list[str] = {
    'hdtv', 'tvrip', '2160p', 
    '1440p', '1080p', '720p',
    '480p', '360p', '4K'
}

class NameParser:
        
    def __init__(self, name:str|None) -> None:
        from .PTN import parse

        if name:
            self._get = parse(name).get
        else:
            self._get = lambda x: None
        
        self.name = name

        self.title: str|None = self._get('title')

    @cached_property
    def season(self) -> list[int]:

        x: int|list[int]|None = self._get('season')

        if x is None:
            return []
        elif isinstance(x, int):
            return [x]
        else:
            return x
        
    @cached_property
    def episode(self) -> list[int]:

        x: int|list[int]|None = self._get('episode')

        if x is None:
            return []
        elif isinstance(x, int):
            return [x]
        else:
            return x

    @cached_property
    def year(self) -> list[int]:
        from re import findall

        m = findall(
            pattern = "(?:19[0-9]|20[0-2])[0-9]",
            string = self.name
        )
        
        if len(m) > 1:
            return list(range(int(m[0]), int(m[-1]) + 1))
        
        elif m:
            return [int(m[0])]
        
        else:
            return []

    @cached_property
    def quality(self) -> None | Literal[*qualities]:
        for quality in qualities:
            if quality in self.name:
                return quality
