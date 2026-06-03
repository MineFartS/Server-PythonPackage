from argparse import ArgumentParser
from ..classtools import singleton
from typing import Callable, Any
from ..json import SupportsJSON
from . import Log

@singleton
class Args(tuple[SupportsJSON]):

    _parser = ArgumentParser()

    _handlers: dict[str, Callable[[str], Any]] = {}

    _defaults: dict[str, Any] = {}

    _cache: dict[str, Any] = {}

    def __new__(cls):
        from ..text import auto_convert
        from sys import argv

        args = (auto_convert(a) for a in argv[1:])

        return super().__new__(cls, args)

    # TODO: Temporary backwards compatibility
    def __call__(self, *_, **__):
        return self

    def Arg(self,
        name: str,
        default: str = None,
        desc: str = None,
        handler: Callable[[str], Any] = lambda x: x
    ) -> None:
        
        self._handlers[name] = handler

        self._defaults[name] = default

        self._parser.add_argument(
            '--'+name,
            default = -1,
            help = desc,
            dest = name,
        )

    def Flag(self,
        name: str,
        letter: str = None,
        desc: str = None,
        invert: bool = False
    ) -> None:
        
        flags = ['--'+name]

        if letter:
            flags.insert(0, '-'+letter)
        
        self._parser.add_argument(
            *flags,
            help = desc,
            dest = name,
            action = 'store_true'
        )

        if invert:
            self._handlers[name] = lambda x: not x
            self._defaults[name] = True
        else:
            self._handlers[name] = lambda x: x
            self._defaults[name] = False

    def __getitem__(self,
        key: str | int
    ):
        
        if isinstance(key, int):
            return super().__getitem__(key)
        
        elif key in self._cache:
            return self._cache[key]

        else:

            parsed = self._parser.parse_known_args()[0]
            
            handler = self._handlers[key]

            rvalue = getattr(parsed, key)
            
            if rvalue == -1:
                
                value = self._defaults[key]
                Log.VERB(f'Parsed Arguement: {key=} | {self._defaults[key]=}')
            
            else:

                value = handler(rvalue)
                Log.VERB(f'Parsed Arguement: {key=} | {rvalue=} | {value=}')

            self._cache[key] = value

            return value

Args.Flag(
    name = 'verbose',
    letter = 'v',
    desc = 'Advanced Debugging'
)