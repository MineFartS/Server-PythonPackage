from typing import Self

#====================================================
# Time Zone
from pytz import timezone as __timezone
TIMEZONE = __timezone('America/New_York')
#====================================================

def sleep(
    s: int,
    show: bool = False
):
    """
    Wrapper for time.Sleep function

    If show is True, then '#/# seconds' will print to the console each second
    """
    from .terminal import ProgressBar
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

    def elapsed(self) -> None | float:
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

    def __int__(self):
        return int(self.elapsed())
    
    __float__ = elapsed

    def __gt__(self, other):
        return self.elapsed() > other

    def __ge__(self, other):
        return self.elapsed() >= other

    def __lt__(self, other):
        return self.elapsed() < other
    
    def __le__(self, other):
        return self.elapsed() <= other
    
    def __eq__(self, other):
        return self.elapsed() == other

class from_stamp:
    """
    Handler for a unix time stamp
    """

    def __init__(self, stamp:int):
        from datetime import datetime
        from functools import partial

        dt = datetime.fromtimestamp(
            timestamp = stamp,
            tz = TIMEZONE
        )

        self.year = dt.year
        """Year (####)"""

        self.month = dt.month
        """Month (1-12)"""
        
        self.day = dt.day
        """Day of the Month (1-31)"""
        
        self.hour = dt.hour
        """Hour (0-23)"""
        
        self.minute = dt.minute
        """Minute (0-59)"""
        
        self.second = dt.second
        """Second (0-59)"""

        self.decisecond = (dt.microsecond // 100000)
        """Decisecond (0-9)"""

        self.centisecond = (dt.microsecond // 10000)
        """Centisecond (0-99)"""

        self.millisecond = (dt.microsecond // 1000)
        """Millisecond (0-999)"""

        self.microsecond = dt.microsecond
        """Microsecond (0-999999)"""

        self.unix = stamp
        """Unix Time Stamp"""

        self.stamp = partial(
            dt.strftime,
            format = "%Y-%m-%d %H:%M:%S"
        )
        """Get Formatted Time Stamp"""

        self.ISO = dt.isoformat()
        """ISO format string"""

    def __int__(self):
        return int(self.unix)
    
    def __float__(self):
        return float(self.unix)
    
    def __repl__(self):
        from .text import abbreviate
        from .classOBJ import loc

        return f"<from_stamp '{abbreviate(30, self.ISO)}' @{loc(self)}>"
    
    __str__ = __repl__

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
    string: str
) -> from_stamp:
    """
    Get details of time string
    """
    from dateutil.parser._parser import ParserError
    from dateutil import parser
    from .classOBJ import path

    try:
    
        dt = parser.parse(string)
        return from_stamp(dt.timestamp())
    
    except OSError, ParserError:
    
        raise TypeError(path(string))

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
