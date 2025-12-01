from math import trunc, floor
from sys import (maxsize as max)

def digit(num:int, i:int) -> int:
    """
    Get digit from number by index

    digit(123, 0) -> 1
    """

    return int( str(num) [i] )

def shuffle_range(min:int, max:int):
    """
    Get a range of numbers, but shuffled
    """
    from .array import List

    ordered = List(range(min, max+1))

    ordered.shuffle()

    return ordered

class valid:
    """
    Check if number is valid
    (int, float)
    """

    def int(num) -> bool:
        """
        Check if number is a valid integer
        """
        try:
            int(num)
            return True
        except ValueError:
            return False

    def float(num) -> bool:
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
