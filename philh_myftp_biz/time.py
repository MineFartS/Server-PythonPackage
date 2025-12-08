from typing import Self

def sleep(
    s: int,
    show: bool = False
):
    """
    Wrapper for time.Sleep function

    If show is True, then '#/# seconds' will print to the console each second
    """
    from .pc import ProgressBar
    from time import sleep

    # If show is True
    if show:

        pbar = ProgressBar(s)
    
        # loop once for each second
        for _ in range(s):

            sleep(1)

            pbar.step()

        pbar.stop()

    else:
        sleep(s)
    
    return True

def toHMS(stamp:int) -> str:
    """
    Convert a unix time stamp to 'hh:mm:ss'
    """

    m, s = divmod(stamp, 60)
    h, m = divmod(m, 60)
    
    return f'{h:02d}:{m:02d}:{s:02d}'

class Stopwatch:
    """
    Keeps track of time
    """

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.running = False

    def elapsed(self) -> None | int:
        """
        Get the # of seconds between now or the stop time, and the start time
        """
        from time import perf_counter

        if self.start_time != None:

            if self.running:
                elapsed = perf_counter() - self.start_time
            else:
                elapsed = self.end_time - self.start_time

            return elapsed

    def start(self) -> Self:
        """
        Start the stopwatch at 0
        """
        from time import perf_counter

        self.start_time = perf_counter()
        self.end_time = None
        self.running = True

        return self

    def stop(self) -> Self:
        """
        Stop the stopwatch
        """
        from time import perf_counter

        self.end_time = perf_counter()
        self.running = False
        
        return self

class from_stamp:
    """
    Handler for a unix time stamp
    """

    def __init__(self, stamp:int):
        from datetime import timezone, timedelta, datetime

        self.__dt = datetime.fromtimestamp(
            timestamp = stamp,
            tz = timezone(
                offset = timedelta(hours=-4)
            )
        )

        self.year:  int = self.__dt.year
        """Year (####)"""

        self.month: int = self.__dt.month
        """Month (1-12)"""
        
        self.day:   int = self.__dt.day
        """Day of the Month (1-31)"""
        
        self.hour:  int = self.__dt.hour
        """Hour (0-23)"""
        
        self.minute:int = self.__dt.minute
        """Minute (0-59)"""
        
        self.second:int = self.__dt.second
        """Second (0-59)"""

        self.unix:  int = stamp
        """Unix Time Stamp"""

        self.stamp = self.__dt.strftime
        """Get Formatted Time Stamp"""

    def __int__(self):
        return int(self.unix)
    
    def __float__(self):
        return float(self.unix)

    def __eq__(self, other):

        if isinstance(other, (from_stamp, int, float)):
            return (self.unix == float(other))
        else:
            return False
        
    def __lt__(self, other):
        from .classOBJ import path

        if isinstance(other, (from_stamp, int, float)):
            return (self.unix < float(other))
        
        else:
            raise TypeError(path(other))
        
    def __gt__(self, other):
        from .classOBJ import path

        if isinstance(other, (from_stamp, int, float)):
            return (self.unix > float(other))
        
        else:
            raise TypeError(path(other))

def now() -> from_stamp:
    """
    Get details of the current time
    """
    from time import time

    return from_stamp(time())

def from_string(
    string: str,
    separator:str = '/',
    order:str = 'YMD'
) -> from_stamp:
    """
    Get details of time string
    """
    from datetime import datetime

    split = string.split(separator)

    order = order.lower()
    Y = split[order.index('y')]
    M = split[order.index('m')]
    D = split[order.index('d')]

    dt = datetime.strptime(f'{Y}-{M}-{D}', "%Y-%m-%d")

    return from_stamp(dt.timestamp())

def from_ymdhms(
    year:   int = 0,
    month:  int = 0,
    day:    int = 0,
    hour:   int = 0,
    minute: int = 0,
    second: int = 0,
) -> from_stamp:
    """
    Get details of time from year, month, day, hour, minute, & second
    """
    from datetime import datetime

    t = datetime(
        year,
        month,
        day,
        hour,
        minute,
        second
    )

    return from_stamp(t.timestamp())
