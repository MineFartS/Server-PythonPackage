from .Collection import Collection
from typing import ItemsView

class Dict[T](Collection[T, dict[str, T]]):
    """dict Wrapper"""
    
    _default = {}

    def __getitem__(self, key) -> None | T:
        
        data = self.read()
        
        if key in data:
            return data[key]
        
    def __iter__(self):
        return iter(self.read().keys())

    def items(self) -> ItemsView[str, T]:
        return self.read().items()
