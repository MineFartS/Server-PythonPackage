from typing import ItemsView, KeysView, ValuesView, Any
from .Collection import Collection

class Dict[T](Collection[T, dict[str, T]]):
    
    _default: dict[str, T] = {}

    def __getitem__(self, key: str) -> T | None:
        data = self.read()
        if key in data:
            return data[key]
        return None

    def items(self) -> ItemsView[str, T]:
        return self.read().items()

    def keys(self) -> KeysView[str]:
        return self.read().keys()

    def values(self) -> ValuesView[T]:
        return self.read().values()

    def get(self, key: str, default: Any = None) -> Any:
        return self.read().get(key, default)

    def update(self, other: dict[str, T] | 'Dict[T]') -> None:
        with self.handle() as data:
            if isinstance(other, Collection):
                other = other.read()
            data.update(other)

