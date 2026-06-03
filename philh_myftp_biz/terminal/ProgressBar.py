from sys import stdout
from . import Log

class Pipe:

    def __init__(self,
        pbar: 'ProgressBar'
    ) -> None:
        self.pbar = pbar

    def write(self, s:str):
        import sys

        if self.pbar.finished:
            sys.stdout = stdout
        else:
            self.pbar.clear()

        #
        stdout.write(s)

    def flush(self):
        pass

class ProgressBar:

    __bar_format = "{n_fmt}/{total_fmt} | {bar} | {elapsed}"

    def __init__(self,
        total: int = 0
    ) -> None:
        from ..process import Thread
        from tqdm import tqdm
        import sys

        self._tqdm = tqdm(
            iterable = range(total),
            bar_format = self.__bar_format,
            dynamic_ncols = True
        )

        self.reset = self._tqdm.reset
        self.stop  = self._tqdm.close
        self.step  = self._tqdm.update
        self.clear = self._tqdm.clear
        self.flush = self._tqdm.refresh

        self.total: int|float = self._tqdm.total

        sys.stdout = Pipe(pbar=self)

        Thread(self.__refresh)

    @property
    def finished(self) -> bool:

        if self._tqdm.total == 0:
            return False
        else:
            return (self._tqdm.n == self._tqdm.total)

    @property
    def running(self):
        return not (self.finished or self._tqdm.disable)
        
    def __refresh(self):
        from time import sleep

        lastval = None

        while self.running:

            # Wait .3 seconds
            sleep(.3)
            
            # Update the timer
            self._tqdm.refresh()

            # Sync the total
            self._tqdm.total = self.total

            if lastval != self._tqdm.n:

                n = self._tqdm.n
                t = self._tqdm.total

                try:
                    p = round(n/t, 2)
                except ZeroDivisionError:
                    p = 0

                Log.VERB(f'ProgressBar: ({p}%, n={n}, t={t})')

                lastval = n
