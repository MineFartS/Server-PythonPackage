from ..functools.supports import SupportsJSON # pyright: ignore[reportUnusedImport]
from json import load, loads, dump, dumps # pyright: ignore[reportUnusedImport]
from .List import List # pyright: ignore[reportUnusedImport]
from .Dict import Dict # pyright: ignore[reportUnusedImport]

def is_json(value:str) -> bool:
    """Check if a string contains valid json data"""
    from json.decoder import JSONDecodeError

    try:
        loads(value)
        return True
    except JSONDecodeError:
        return False
