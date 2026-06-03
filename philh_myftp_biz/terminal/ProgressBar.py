from typing import Literal, Iterable
from ..classtools import singleton
from ..functools import NullSafe
from ..num import nlen
import sys

@singleton
class Pipe:

    def __init__(self) -> None:
        from ..process import Looper
        
        self.stdout = sys.stdout
        self.flush = sys.stdout.flush
        sys.stdout = self

        self.pbar: ProgressBar = None

        Looper(
            lambda: NullSafe(self.pbar).refresh(),
            interval = .5
        )

    def write(self, s:str) -> None:

        if self.pbar:
            self.pbar.tqdm.write(s, self.stdout)
        else:
            self.stdout.write(s)

_modes = Literal[
    'SCOUNTER', # Simple Counter
    'FCOUNTER', # Full Counter
    'FSTREAM' # FIle Stream
]

class ProgressBar:

    def __init__(self,
        total: int|float|Iterable = 0,
        *,
        mode: _modes = 'SCOUNTER',
        label: None|str = None,
        verbose: bool = False
    ) -> None:
        from .. import VERBOSE
        from tqdm import tqdm
        
        kwargs: dict = {
            "dynamic_ncols": True,
            "disable": (verbose and not VERBOSE),
            "total": nlen(total),
            "desc": label
        }

        match mode:

            case 'SCOUNTER':
                kwargs['bar_format'] = "{n_fmt}/{total_fmt} | {bar} | {elapsed}"

            case 'FSTREAM':
                kwargs['unit'] = "B"
                kwargs['unit_scale'] = True

        self.tqdm = tqdm(**kwargs)

        Pipe.pbar = self

    def step(self,
        n: int|float|Iterable = 1
    ) -> None:
        
        Pipe.pbar = self
        
        self.tqdm.update(nlen(n))

    def stop(self) -> None:

        if Pipe.pbar == self:
            Pipe.pbar = None

        self.tqdm.clear()
        self.tqdm.close()

    def refresh(self) -> None:

        Pipe.pbar = self

        self.tqdm.clear()
        self.tqdm.refresh()

    @property
    def finished(self) -> bool:

        if self.tqdm.total == 0:
            return False
        else:
            return (self.tqdm.n == self.tqdm.total)

    @property
    def running(self) -> bool:
        return not (self.finished or self.tqdm.disable)

