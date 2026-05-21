from typing import Callable

class SharedBuffer:

    stop_when: Callable[[], bool] = lambda: False
    """
    Is called before each iteration
    Will stop iteration if returns True 
    """

    def __init__(self) -> None:
        
        self.entries = []

        self.__iadd__ = self.entries.append

        self.add = self.entries.append

    def __iter__(self):
        return self

    def __next__(self):

        if self.stop_when():

            raise StopIteration()
        
        else:

            while len(self.entries) == 0:
                pass

            entry = self.entries[0]

            del self.entries[0]

            return entry
