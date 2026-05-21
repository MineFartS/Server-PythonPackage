from typing import (
    runtime_checkable, Protocol,
    SupportsInt, SupportsFloat, SupportsBytes 
) # pyright: ignore[reportUnusedImport]

#========================================================

@runtime_checkable
class SupportsStr(Protocol):
    def __str__(self) -> str:
        ...

#========================================================

SupportsJSON = \
    str| \
    int| \
    float| \
    bool| \
    None| \
    dict[str, "SupportsJSON"]| \
    list["SupportsJSON"]

#========================================================