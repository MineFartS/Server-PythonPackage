"""Wrapper for hexadecimal via dill"""

def valid(string:str) -> bool:
    """Check if string is a valid dill hexadecimal dump"""

    try:
        decode(string)
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
    """Convert any pickleable object into a string"""
    from dill import dumps
    
    return dumps(value).hex()
