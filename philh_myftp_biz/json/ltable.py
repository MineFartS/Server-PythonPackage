class LookupTable:

    def __init__[K,V](self, data:dict[K,V]) -> None:

        fdata = data.copy()
        rdata = {v: k for k, v in fdata.items()}

        self.val = fdata.__getitem__
        """Get value by key"""
        
        self.key = rdata.__getitem__
        """Get key by value"""
    