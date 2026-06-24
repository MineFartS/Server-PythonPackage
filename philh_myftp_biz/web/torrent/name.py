from functools import cached_property

qualities: list[str] = {
    'hdtv', 'tvrip', '2160p', 
    '1440p', '1080p', '720p',
    '480p', '360p', '4K'
}

class NameParser:
        
    def __init__(self, name:str) -> None:
        from PTN import parse

        self._get = parse(name).get
        
        self.name = name

        self.title: str|None = self._get('title')

        self.season: int|list[int]|None = self._get('season')

        self.episode: int|list[int]|None = self._get('episode')

    @cached_property
    def year(self) -> list[int] | int | None:
        from re import findall

        if self._get('year'):
            return self._get('year')

        m = findall(
            pattern = "(?:19[0-9]|20[0-2])[0-9]",
            string = self.name
        )
        
        if len(m) > 1:

            years = list(range(int(m[0]), int(m[-1]) + 1))
            
            if len(years) > 0:
                return years
        
        elif m:
            return int(m[0])

    @cached_property
    def quality(self) -> None | str:
        for quality in qualities:
            if quality in self.name:
                return quality
