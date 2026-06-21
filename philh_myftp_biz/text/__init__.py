from typing import Callable
from functools import cache

from fnmatch import fnmatch as like # pyright: ignore[reportUnusedImport]

from . import contains, hex # pyright: ignore[reportUnusedImport]
from .regex import Pattern # pyright: ignore[reportUnusedImport]
from .io import UnconsumingIO # pyright: ignore[reportUnusedImport]

def split(
    value: str,
    sep: str = None
) -> list[str]:
    """
    Automatic String Splitter

    If sep is None, then shlex.split is used.
    If sep is defined, then str.split is used
    """
    import shlex
    
    # If a sep is declared
    if sep:
        # Split the value by sep
        return value.split(str(sep))
    else:
        # Automatically split the value using based on shell syntax
        return shlex.split(value)

def int_stripper(string:str) -> None | int:
    """Remove all non-numerical characters from an alphanumeric string"""
    from ..num import is_int

    # Copy the string
    string = str(string)

    # Iter through all chaacters in the string
    for char in string:

        # If the character is not an integer
        if not is_int(char):

            # Remove the character from the string
            string = string.replace(char, '')

    # Output the string as an integer
    if len(string) > 0:
        return int(string)

@cache
def auto_convert(string:str) -> int | float | bool | dict | str:
    """
    Automatically convert string

    Input Types:
        - int
        - float
        - bool
        - hex (dill)
        - dict
        - str
    """

    from ..num import is_int, is_float
    from ..json import is_json, loads

    if is_int(string):
        return int(string)
    
    elif is_float(string):
        return float(string)
    
    elif string.lower() in ['true', 'false']:
        return bool(string)
    
    elif hex.valid(string):
        return hex.decode(string)
    
    elif is_json(string):
        return loads(string)
 
    else:
        return string

def random(length:int) -> str:
    """
    Get a string with random characters

    Ex: random(6) -> 'JAIOEN'
    """
    from random import choices
    from string import ascii_uppercase, digits

    return ''.join(choices(
        population = ascii_uppercase + digits,
        k = length
    ))

def rm_emojis(
    text: str,
    sub: str = ''
) -> str:
    """
    Remove all emojis from a string
    """
    from re import compile, UNICODE

    regex = compile(
        "["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "]+",
        flags = UNICODE
    )

    return regex.sub(
        repl = sub.encode('unicode_escape').decode(),
        string = text.encode('utf-8').decode()
    )

def similarity(
    a: str,
    b: str
) -> float:
    """
    Get the percentage of how similar two strings are

    Ex: similarity('hi', 'hi') -> 1.0
    """
    from difflib import SequenceMatcher

    return SequenceMatcher(None, str(a), str(b)).ratio()

@cache
def abbr(
    num: int,
    string: str,
    inclusive: bool = True,
    end: str = '...'
) -> str:
    
    # Copy the string
    string = str(string)

    if len(string) <= num:
        return string
    
    elif inclusive:
        return string[:num-len(end)] + end

    else:
        return string[:num] + end

def from_function(func: Callable) -> None | str:
    from inspect import getsourcelines

    line = ''.join(getsourcelines(func)[0]).strip()

    return 'lambda' + line.split('lambda', 1)[1]

@cache
def to_slice(string:str) -> None | list[slice|int]:
    """
    Parse a string into a list of slices or integers

    EXAMPLES:
    ```
    '.'    : [:]
    '7'    : 7
    '..3'  : [:4]
    '5..'  : [5:]
    '3..5' : [3:6]
    '1,3'  : 1, 3
    ```
    """
    from ..num import is_int

    if string == '.':

        return [slice(0, None)]

    elif is_int(string):

        return [int(string)]
    
    elif ',' in string:

        slices = []

        for part in string.split(','):

            _slice: list = to_slice(part)

            if _slice:
                slices += _slice
            else:
                return
        
        return slices

    elif string.startswith('..'):

        return [slice(
            0, 
            int(string[2:])+1
        )]
    
    elif string.endswith('..'):

        return [slice(
            int(string[:-2]),
            None 
        )]

    elif '..' in string:
    
        parts = string.split('..')

        return [slice(
            int(parts[0]),
            int(parts[1])+1
        )]

def recode(string:str):
    return string.encode(errors='ignore').decode()