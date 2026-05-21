
def any(
    string: str,
    values: list[str],
    case: bool = False
) -> bool:
    """Check if string contains any of the values"""
    
    if not case:
        string = string.lower()
        values = [str(v).lower() for v in values]

    # Iter through all passed values
    for v in values:

        # If the string contains the value
        if v in string:

            # Return True
            return True
        
    # If no values are matched, then return False
    return False

def all(
    string: str,
    values: list[str],
    case: bool = False
) -> bool:
    """Check if string contains all of the values"""

    if not case:
        string = string.lower()
        values = [str(v).lower() for v in values]

    # Iter through all passed values
    for v in values:

        # If the string does not contain the value
        if v not in string:

            # Return False
            return False
        
    # If all values are matched, then return True
    return True
