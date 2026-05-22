from typing import Callable, Union, TypeAlias, TypeVar
from .json.List import List # TODO: Temporary Backwards Compatibility

_T = TypeVar('_T')

SortFunc: TypeAlias = Callable[
    [_T],
    Union[
        int, 
        float, 
        list[int | float], 
        tuple[int | float]
    ]
]

FilterFunc: TypeAlias = Callable[[_T], bool]

#========================================================

def copy(
    array: list|tuple
) -> list:
    
    if isinstance(array, list):
        return array.copy()
    
    else:
        return list(array[:])

def stringify(array:list) -> list[str]:

    array = copy(array)

    for x, item in enumerate(array):
        array[x] = str(item)

    return array

def intify(array:list) -> list[int]:

    array = copy(array)

    for x, item in enumerate(array):
        array[x] = int(item)

    return array

#========================================================

def overlap(
    list1: list,
    list2: list
) -> bool:
    return not set(list1).isdisjoint(list2)

#========================================================
