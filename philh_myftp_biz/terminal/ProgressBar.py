from typing import Callable, Literal
from tqdm import tqdm
import sys

from ..classtools import singleton

@singleton
class Pipe:

    def __init__(self) -> None:
        
        self.stdout = sys.stdout
        self.flush = sys.stdout.flush
        sys.stdout = self

        self.pbar: None|ProgressBar = None

    def write(self, s:str) -> None:

        if self.pbar:
            self.pbar.clear()

        self.stdout.write(s)

_modes = Literal[
    'SCOUNTER', # Simple Counter
    'FCOUNTER', # Full Counter
    'FILE STREAM'
]

class ProgressBar(tqdm):

    def __init__(self,
        total: int = 0,
        mode: _modes = 'SCOUNTER'
    ) -> None:
        from ..process import Thread
        
        kwargs: dict = {
            "dynamic_ncols": True,
        }

        match mode:

            case 'SCOUNTER':
                kwargs['iterable'] = range(total)
                kwargs['bar_format'] = "{n_fmt}/{total_fmt} | {bar} | {elapsed}"

            case 'FCOUNTER':
                kwargs['iterable'] = range(total)

            case 'FILE STREAM':
                kwargs['total'] = total
                kwargs['unit'] = "B"
                kwargs['unit_scale'] = True

        super().__init__(**kwargs)

        self.stop  = self.close
        self.step  = self.update
        self.flush: Callable[..., None] = self.refresh

        Pipe.pbar = self

        Thread(self.__refresh)

    @property
    def finished(self) -> bool:

        if self.total == 0:
            return False
        else:
            return (self.n == self.total)

    @property
    def running(self) -> bool:
        return not (self.finished or self.disable)

    def __refresh(self) -> None:
        from time import sleep

        while self.running:
            sleep(.3)
            self.refresh()
