from typing import Callable

class Thread[T]:

    result: T

    @property
    def _Builder(self):
        from threading import Thread
        return Thread

    def __init__(self,
        func: Callable[..., T],
        *args: str,
        **kwargs: str
    ) -> None: 

        self._Builder.run = lambda s: setattr(
            self, 
            'result', 
            s._target(*s._args, **s._kwargs)
        )

        # Create new thread
        self.p = self._Builder(
            target = func,
            kwargs = kwargs,
            args = args
        )

        # Close when main execution ends
        self.p.daemon = True

        # start the task
        self.p.start()

        self.wait = self.p.join

        self.running: bool = property(self.p.is_alive)

    def read(self,
        timeout: int,
        default: T = None
    ) -> T:
        from ..time import Timeout

        to = Timeout(timeout)

        while True:

            if 'result' in self.__dict__:
                return self.result
            
            elif to.timed_out:
                return default

class MProcess(Thread):

    @property
    def _Builder(self):
        from multiprocessing import Process
        return Process

class Sleeper:
    """Call a function before exiting after main thread has ended"""

    def __init__(self,
        func: Callable,
        *args: str,
        **kwargs: str
    ) -> None:
        from threading import Thread

        self.func = func
        self.args = args
        self.kwargs = kwargs

        # Create new thread
        self._thread = Thread(target=self._main)
        
        self._thread.start()

    def _main(self) -> None:
        from time import sleep

        while Alive():
            sleep(.1)

        self.func(*self.args, **self.kwargs)

def Alive() -> bool:
    """Check if the main thread is running"""
    from threading import main_thread

    return main_thread().is_alive()
