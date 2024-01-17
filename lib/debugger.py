import re
import sys

class Debugger:

    DEBUGGER_WIDTH = 300
    DEBUGGER_KEY_WIDTH = 30
    DEBUGGER_SHOW_DICT = True
    DEBUGGER_SHOW_LIST = True
    DEBUGGER_SHOW_CONTEXT = True
    DEBUGGER_SHOW_DECORATOR = True
    DEBUGGER_SHOW_ERROR = True

    _DEBUGGER_COLORS = {
    'reset': '\x1b[0m',               'bold': '\x1b[1m',              'italic': '\x1b[3m',                'underline': '\x1b[4m', 
    'inverse': '\x1b[7m',             'black': '\x1b[30m',            'red': '\x1b[31m',                  'green': '\x1b[32m',
    'yellow': '\x1b[33m',             'blue': '\x1b[34m',             'magenta': '\x1b[35m',              'cyan': '\x1b[36m',
    'white': '\x1b[37m',              'gray': '\x1b[90m',             'bright_red': '\x1b[91m',           'bright_green': '\x1b[92m',
    'bright_yellow': '\x1b[93m',      'bright_blue': '\x1b[94m',      'bright_magenta': '\x1b[95m',       'bright_cyan': '\x1b[96m',
    'bright_white': '\x1b[97m',       'bg_black': '\x1b[40m',         'bg_red': '\x1b[41m',               'bg_green': '\x1b[42m',
    'bg_yellow': '\x1b[43m',          'bg_blue': '\x1b[44m',          'bg_magenta': '\x1b[45m',           'bg_cyan': '\x1b[46m',
    'bg_white': '\x1b[47m',           'bg_gray': '\x1b[100m',         'bg_bright_red': '\x1b[101m',       'bg_bright_green': '\x1b[102m',
    'bg_bright_yellow': '\x1b[103m',  'bg_bright_blue': '\x1b[104m',  'bg_bright_magenta': '\x1b[105m',   'bg_bright_cyan': '\x1b[106m',
    'bg_bright_white': '\x1b[107m',   'default': '\x1b[49m',           'bg_bright_black': '\x1b[100m',
    }

    _DEBUGGER_SCHEMAS = {
        'blue': {'header_color':'white', 'background_color': 'bg_bright_blue', 'color': 'blue'},
        'green': {'header_color':'white', 'background_color': 'bg_bright_green', 'color': 'green'},
        'yellow': {'header_color':'white', 'background_color': 'bg_bright_yellow', 'color': 'yellow'},
        'cyan': {'header_color':'white', 'background_color': 'bg_bright_cyan', 'color': 'cyan'},
        'magenta': {'header_color':'white', 'background_color': 'bg_bright_magenta', 'color': 'magenta'},
        'red': {'header_color':'white', 'background_color': 'bg_bright_red', 'color': 'red'},
        'gray': {'header_color':'white', 'background_color': 'bg_gray', 'color': 'gray'},
        'white': {'header_color':'gray', 'background_color': 'bg_white', 'color': 'white'},
        'default': {'header_color':'white', 'background_color': 'bg_bright_black', 'color': 'white'},
    }

    def __init__(self, tag= None, color_schema=None):
        self.tag = tag
        self.color_schema = color_schema
        self.active = False

    def test(self):
        for key in Debugger._DEBUGGER_COLORS.keys():
            print(f"{Debugger._DEBUGGER_COLORS[key]}{key}{Debugger._DEBUGGER_COLORS['reset']}")

    def _reset(self):
        print(f"{Debugger._DEBUGGER_COLORS['reset']}",end='')
        print(f"{Debugger._DEBUGGER_COLORS['bg_black']}",end='')

    def _header_color(self,schema):
        print(f"{Debugger._DEBUGGER_COLORS[Debugger._DEBUGGER_SCHEMAS[schema]['background_color']]}",end='')
        print(f"{Debugger._DEBUGGER_COLORS[Debugger._DEBUGGER_SCHEMAS[schema]['header_color']]}",end='')

    def _color(self,schema):
        self._reset()
        print(f"{Debugger._DEBUGGER_COLORS[Debugger._DEBUGGER_SCHEMAS[schema]['color']]}",end='')

    def _context(self,func):
        if Debugger.DEBUGGER_SHOW_CONTEXT and func and func.__name__ and func.__globals__:
            self._header_color(self.color_schema)
            print(f"{func.__globals__['__name__']}.{func.__name__}{Debugger._DEBUGGER_COLORS['reset']}")

    def _cutoff(self,value):
        _value = str(value)
        return f"{value[:(Debugger.DEBUGGER_WIDTH - 3)]}..." if len(_value) > Debugger.DEBUGGER_WIDTH else f"{_value}"

    def showList(self, *args, use_schema=True):
        if Debugger.DEBUGGER_SHOW_LIST and args and len(args)>1:
            if use_schema:
                self._color(self.color_schema)
            else:
                self._color('gray')
            _spacer = ' ' * 2
            for arg in args[1:]:
                if type(arg) == bytes:
                    _arg = f"b'{arg.decode()}'"
                else:
                    _arg = str(arg)
                if re.match(r'^<\?xml',_arg):
                    _arg = re.sub('><', f">\n{_spacer}<", self._cutoff(_arg))
                else:
                    _arg = re.sub('[\r\n]+', f"\n{_spacer}", self._cutoff(_arg))
                print(_spacer + _arg)

    def _ljust(self,string, fixed_length):
        return string + " " * (fixed_length - len(string))

    def showDict(self,use_schema=True, **kwargs):
        if Debugger.DEBUGGER_SHOW_DICT and kwargs and len(kwargs):
            for (key,value) in kwargs.items():
                _spacer = ' ' * (Debugger.DEBUGGER_KEY_WIDTH + 4)
                _arg = re.sub('[\r\n]+', f"\n{_spacer}" , self._cutoff(str(value)))
                if use_schema:
                    self._color(self.color_schema)
                else:
                    self._color('gray')
                print(f"{Debugger._DEBUGGER_COLORS['bold']}", end='')
                print(f"  {self._ljust(key,Debugger.DEBUGGER_KEY_WIDTH)}: ",end='')
                if use_schema:
                    self._color(self.color_schema)
                else:
                    self._color('gray')
                print(_arg)

    def error(self,description):
        if self.active and Debugger.DEBUGGER_SHOW_ERROR:
            self._header_color('red')
            print("ERR:",end='')
            self._color('red')
            print(description)
            self._color('default')

    def show(self,func):
        def wrapper(*args, **kwargs):
            if self.active and Debugger.DEBUGGER_SHOW_DECORATOR:
                self._context(func)
                self.showList(*args)
                self.showDict(**kwargs)
                self._reset()
                return func(*args, **kwargs)
        return wrapper
    