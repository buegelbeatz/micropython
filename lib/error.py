from debugger import Debugger

debug = Debugger(color_schema='red')
debug.active = True

def exception(func):
    def wrapper(*args, **kwargs):
        if debug.active is True:
            _result = None
            try:
                _result = func(*args, **kwargs)
            except Exception as e:
                debug.context(func)
                debug.error(e)
            return _result
        else:
            return func(*args, **kwargs)
    return wrapper