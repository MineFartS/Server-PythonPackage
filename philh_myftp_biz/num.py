from sys import maxsize as maxint
from math import trunc, floor
from typing import Literal

#========================================================

def digit(num:int, i:int) -> int:
    """
    Get digit from number by index

    digit(123, 0) -> 1
    """

    return int( str(num) [i] )

def shuffle_range(
    MIN: int,
    MAX: int
):
    """
    Get a range of numbers, but shuffled
    """
    from .array import List

    ordered = List(range(MIN, MAX+1))

    ordered.shuffle()

    return ordered

def clamp(
    x:   int|float,
    MIN: int|float,
    MAX: int|float
):
    """
    Clamp a number to a range
    """
    return max(min(x, MAX), MIN)

def flop(
    x1: float,
    op: Literal['+', '-', '*', '/'],
    x2: float
):
    """
    Perform floating point operations without rounding

    Example:
    ```
    >>> .1 + .2
    0.30000000000000004

    >>> flop(.1, '+', .2)
    .3
    ```
    """
    
    SCALE = 10 ** max(
        len(str(x1).split('.')[1]),
        len(str(x2).split('.')[1])
    )

    # Scale the floats to integers
    _x1 = int(x1 * SCALE)
    _x2 = int(x2 * SCALE)

    match op:

        case '+':
            return (_x1 + _x2) / SCALE

        case '-':
            return (_x1 - _x2) / SCALE
    
        case '*':
            return (_x1 * _x2) / SCALE
    
        case '/':
            return (_x1 / _x2)
    
        case _:
            raise NotImplementedError(f'{op=}')

def nearest_multiple(
    x: int|float,
    multiple_of: int
) -> int:
    """
    Snap x to the nearest multiple of a number

    EXAMPLES:
    ```
    >>> nearest_multiple(17, 8)
    16

    >>> nearest_multiple(22, 10)
    20
    ```
    """

    return x//multiple_of * multiple_of

#========================================================

def is_int(num) -> bool:
    """
    Check if number is a valid integer
    """
    try:
        int(num)
        return True
    except ValueError:
        return False

def is_float(num) -> bool:
    """
    Check if a number is a valid float
    """
    try:
        float(num)
        return True
    except ValueError:
        return False

def is_prime(num) -> bool:
    """
    Check if a number is a prime number
    """

    pre = {
        0: False,
        1: False,
        2: True
    }

    if num in pre:
        return pre[num]

    else:

        if digit(num, -1) in [0, 2, 4, 5, 6, 8]:
            return False
        
        else:
            for i in range(2, num):
                if (num % i) == 0:
                    return False

            return True

#========================================================