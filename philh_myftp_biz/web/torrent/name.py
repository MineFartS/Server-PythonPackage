from functools import cached_property
from typing import Any

qualities: tuple[str] = (
    'hdtv', 'tvrip', '2160p', 
    '1440p', '1080p', '720p',
    '480p', '360p', '4K'
)

class NameParser:
        
    def __init__(self, name:str|None) -> None:
        from PTN import parse

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
    def quality(self) -> None | str:
        for quality in qualities:
            if quality in self.name:
                return quality

class Weights(dict[str, Any]):
    """```

    class WeightsImpl(Weights):
        def TITLE(self, sample, control):
            return (sample == control)

    w = WeightsImpl()
    w['TITLE'] = "Hello"
    w.parse("Hello") -> True
    ```"""
    
    def parse(self, name:str) -> bool:
        from ...terminal import Log

        parse = NameParser(name)

        logm: str = f'Validating: {name}'

        valid = True

        for key, control in self.items():

            sample = getattr(parse, key.lower())

            _valid = getattr(self, key)(
                sample = sample,
                control = control
            )

            valid &= _valid

            logm += f'\n{key}={_valid:d} | {sample=} | {control=}'

        logm += f'\n{valid=}'
 
        Log.VERB(logm)

        return valid

    def TITLE(self,
        sample: str | None,
        control: list[str|None]
    ) -> bool:
        from ...text import similarity
        return any(similarity(sample, c)>.65 for c in control)

    def SEASON(self,
        sample: list[int], 
        control: int
    ) -> bool:
        return (control in sample)
        
    def YEAR(self,
        sample: list[int], 
        control: int
    ) -> bool:
        return (len(sample) == 0) or (control in sample)

    def EPISODE(self,
        sample: list[int], 
        control: int | None
    ) -> bool:
        if len(sample) > 0:
            return control == sample[0]
        else:
            return control is None

