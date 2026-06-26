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

class MProcess[T](Thread[T]):

    @property
    def _Builder(self):
        from multiprocessing import Process
        return Process

class Sleeper(Thread[None]):
    """Call a function before exiting after main thread has ended"""

    def __init__(self,
        func: Callable,
        *args: str,
        **kwargs: str
    ) -> None:

        self.func = func
        self.args = args
        self.kwargs = kwargs

        super().__init__(self._main)

    def _main(self) -> None:
        from time import sleep

        while Alive():
            sleep(.1)

        self.func(*self.args, **self.kwargs)

class Watcher[T](Thread):

    def __init__(self,
        checker: Callable[[], T],
        handler: Callable[[T], None],
        interval: int|float = .3
    ) -> None:
        
        self.checker = checker
        self.handler = handler
        self.interval = interval

        super().__init__(self._main)

    def _main(self) -> None:
        from inspect import signature
        from ..time import sleep

        lvalue: T = None

        try:
            params = signature(self.handler).parameters
        except TypeError:
            params = []
        
        while sleep(self.interval):

            value = self.checker()

            if value != lvalue:

                lvalue = value

                if len(params) == 0:
                    self.handler()
                else:
                    self.handler(value)                    

class Looper(Watcher):

    def __init__(self,
        func: Callable[[], None],
        interval: int|float = .3
    ) -> None:
        from ..time import now

        super().__init__(
            checker = now, 
            handler = func,
            interval = interval
        )

def Alive() -> bool:
    """Check if the main thread is running"""
    from threading import main_thread

    return main_thread().is_alive()

class ThreadedFunc:
    
    def __init__(self, func) -> None:
        from functools import wraps

        self.func: Callable = func
        self.thread: Thread = None

        wraps(func)(self)

    def __call__(self, *args, **kwargs):
        
        if self._thread is None:
        
            self._thread = Thread(
                func=self.func, 
                args=args, 
                kwargs=kwargs
            )
            
        return self._thread

