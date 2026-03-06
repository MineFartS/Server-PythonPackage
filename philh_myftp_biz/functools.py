
def single_use(f): # pyright: ignore[reportMissingParameterType]
    """Ignore all but first executions"""
    from functools import wraps

    @wraps(f)
    def wrapper(*args, **kwargs): # pyright: ignore[reportMissingParameterType]
        
        if not wrapper.has_run:
            
            wrapper.has_run = True
            
            return f(*args, **kwargs)
    
    wrapper.has_run = False

    return wrapper