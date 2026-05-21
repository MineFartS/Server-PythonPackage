from dataclasses import dataclass

@dataclass
class Absorber[T]:
    """Returns all getattribute requests with a blank function that absorbs all params"""

    returns: T = lambda *args, **kwargs: None

    def __call__(self, *args, **kwargs) -> T:
        return self.returns

    __getattr__ = __call__

    __getitem__ = __call__

    __setitem__ = __call__

    __setitem__ = __call__

