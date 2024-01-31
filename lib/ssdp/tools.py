import utime
import ubinascii
import machine
import re

def wrapper(f):
    return lambda f:f

def format_str(source, **kwargs):
    if source:
        for (key,value) in kwargs.items():
            _replace ="{" + key + "}"
            source = source.replace(_replace, str(value))
        return source
    else:
        return ''

# async def format_str_stream(source, **kwargs): # TODO: Could also be streamed: load_from_path_stream
#     _parameter_pattern = re.compile(r"^.*\{[^\s]+\}.*$")
#     for _line in source.split('\n'):
#         if len(_line) > 0 and _parameter_pattern.match(_line):
#             yield format_str(_line, **kwargs)
#         else:
#             yield _line

def get_mac():
    return ubinascii.hexlify(machine.unique_id()).decode()

def headers_to_dict(raw_headers):
    headers_dict = {}
    header_lines = raw_headers.splitlines()
    headers_dict["_CMD"] = header_lines[0]
    for line in header_lines:
        parts = line.split(': ', 1)
        if len(parts) == 2:
            key = parts[0].lower()
            value = parts[1]
            headers_dict[key] = value
    return headers_dict

def get_hex(key, source):
    if not re.match(r"^hex(_\d+)+$",key):
        return ""
    _parts = key.split("_")
    _result = []
    _start = 0
    for _part in _parts:
        if _part != 'hex':
            if (int(_part)+_start) > len(source):
                _start = 0
            _result.append(source[_start:(int(_part)+_start)])
            _start = _start + int(_part)
    return '-'.join(_result)

def load_from_path(path):
    with open(path,'r',encoding='utf-8') as f:
        _data = f.read()
    return _data

def date():
    timetuple = utime.gmtime()
    return '%s, %02d %s %04d %02d:%02d:%02d %s' % (
        ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][timetuple[6]],
        timetuple[2], ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
            'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][timetuple[1] - 1],
        timetuple[0], timetuple[3], timetuple[4], timetuple[5],
        'GMT')

def dict_include(*args, **kwargs):
    return {k:v for (k,v) in kwargs.items() if k in args}

def dict_exclude(*args, **kwargs):
    return {k:v for (k,v) in kwargs.items() if k not in args}

def enum(**enums: int):
    return type('Enum', (), enums)