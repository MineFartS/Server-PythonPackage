
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
    """
    Remove all non-numerical characters from an alphanumeric string
    """
    from .num import valid

    # Copy the string
    string = str(string)

    # Iter through all chaacters in the string
    for char in string:

        # If the character is not an integer
        if not valid.int(char):

            # Remove the character from the string
            string = string.replace(char, '')

    # Output the string as an integer
    if len(string) > 0:
        return int(string)

class contains:
    """
    Functions to check if text contains value(s) with list as input
    """

    def any (
        string: str,
        values: list[str]
    ) -> bool:
        """
        Check if string contains any of the values
        """

        # Iter through all passed values
        for v in values:

            # If the string contains the value
            if v in string:

                # Return True
                return True
            
        # If no values are matched, then return False
        return False
    
    def all (
        string: str,
        values: list[str]
    ) -> bool:
        """
        Check if string contains all of the values
        """

        # Iter through all passed values
        for v in values:

            # If the string does not contain the value
            if v not in string:

                # Return False
                return False
            
        # If all values are matched, then return True
        return True

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

    from . import num, json

    if num.is_int(string):
        return int(string)
    
    elif num.is_float(string):
        return float(string)
    
    elif string.lower() in ['true', 'false']:
        return bool(string)
    
    elif hex.valid(string):
        return hex.decode(string)
    
    elif json.valid(string):
        return json.loads(string)
 
    else:
        return string

class hex:
    """
    Wrapper for hexadecimal via dill
    """

    def valid(string:str) -> bool:
        """
        Check if string is a valid dill hexadecimal dump
        """

        try:
            hex.decode(string)
            return True
        except (EOFError, ValueError):
            return False

    def decode(value:str):
        """
        Convert hexadecimal string back into original value

        Trims input by ';' before processing
        Ex: 'abc;defg;hij' -> 'defg'

        """
        from dill import loads

        if ';' in value:
            value = value.split(';')[1]

        return loads(bytes.fromhex(value))

    def encode(value) -> str:
        """
        Convert any pickleable object into a string
        """
        from dill import dumps
        
        return dumps(value).hex()

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

def starts_with_any (
    text: str,
    values: list[str]
) -> bool:
    """
    Check if string starts with any of values
    """
    return any([text.startswith(v) for v in values])

def ends_with_any (
    text: str,
    values: list[str]
) -> bool:
    """
    Check if string ends with any of values
    """

    return any([text.endswith(v) for v in values])

def rm_emojis(
    text: str,
    sub: str = ''
):
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

def abbreviate(
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
    