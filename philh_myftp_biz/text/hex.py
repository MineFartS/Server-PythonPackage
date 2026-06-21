"""Wrapper for hexadecimal via dill"""

def valid(string:str) -> bool:
    from _pickle import UnpicklingError
    """Check if string is a valid dill hexadecimal dump"""

    try:
        decode(string)
        return True
    except EOFError, ValueError, UnpicklingError:
        return False

def decode(value:str):
    """Convert hexadecimal string back into original value"""
    from dill import loads

    return loads(bytes.fromhex(value))

def encode(value) -> str:
    """Convert any pickleable object into a string"""
    from dill import dumps
    
    return dumps(value).hex()
