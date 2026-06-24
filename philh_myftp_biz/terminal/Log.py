"""```
VERB: 10
INFO: 20
MAIN: 25
WARN: 30
FAIL: 40
CRIT: 50
```"""
from functools import partial
from typing import Any
from logging import log

def _log(
    msg: Any = '',
    exc_info: Any = None,
    level: int = None
) -> None:
    log(
        level = level, 
        msg = msg, 
        exc_info = exc_info
    )

VERB = partial(_log, level=10)

INFO = partial(_log, level=20)

MAIN = partial(_log, level=25)

WARN = partial(_log, level=30)

FAIL = partial(_log, level=40)

CRIT = partial(_log, level=50)

def on_call(func, logger=VERB):
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        
        logger(f"Calling '{func.__name__}'\n{args=}\n{kwargs=}")
        
        return func(*args, **kwargs)
            
    return wrapper