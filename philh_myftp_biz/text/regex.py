from ..functools.supports import SupportsStr

class Pattern:

    def __init__(self, *patterns):
        self.patterns = patterns

    def __call__(self, string:SupportsStr):
        from re import findall

        items = []
 
        for pattern in self.patterns:
            items += findall(pattern, str(string))
    
        return tuple(items)
