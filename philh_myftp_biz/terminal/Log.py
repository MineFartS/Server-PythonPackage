"""```
VERB: 10
INFO: 20
MAIN: 25
WARN: 30
FAIL: 40
CRIT: 50
```"""
from functools import partial, wraps
from ..functools import cpath
from logging import log
from typing import Any

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

def on_call(func=None, *, logger=VERB):
    
    def decorator(f):
        
        @wraps(f)
        def wrapper(*args, **kwargs):
            logger(f"Calling '{f.__name__}'\n{args=}\n{kwargs=}")
            return f(*args, **kwargs)
        return wrapper

    if func is None: # WITH parentheses
        return decorator
    else: # WITHOUT parentheses
        return decorator(func)
