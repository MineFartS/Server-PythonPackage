from sys import maxsize as max
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
    min: int,
    max: int
):
    """
    Get a range of numbers, but shuffled
    """
    from .array import List

    ordered = List(range(min, max+1))

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

    # Get x # of digits to scale by (y*10^x)
    scale = max(
        len(str(x1).split('.')[1]),
        len(str(x2).split('.')[1])
    )

    # Scale the floats to integers
    _x1 = int(x1 * 10**scale)
    _x2 = int(x2 * 10**scale)

    # Evaluate the expression
    y = eval(f'{_x1} {op} {_x2}')

    # If the operation is not division
    if op != '/':

        # Scale the result back to a float
        y /= 10**scale

    return y

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