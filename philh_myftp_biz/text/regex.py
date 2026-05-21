from ..functools.supports import SupportsStr

class Pattern:

    def __init__(self, *patterns):
        self.patterns = patterns

    def __call__(self, string:SupportsStr):
        from re import findall

        _string = str(string)

        items = []
 
        for pattern in self.patterns:
            items += findall(pattern, _string)
    
        return tuple(items)
    
    @staticmethod
    def from_wildcard(*strings):
        from fnmatch import translate
        
        patterns = []

        for wc in strings:
            patterns += [translate(wc)]
        
        return Pattern(*patterns)

