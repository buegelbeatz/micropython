from . import static
import re
import time
from .base import Exception404
from .request import Request

def _log(*data):
    # print('http.template', *data)
    pass

class HTTPTemplate(static.HTTPStatic):

    REGEXP_COMMAND = re.compile('^\s*\{%\s*(.*?)\s*%\}\s*$')
    REGEXP_INCLUDE = re.compile('^include\s+[\'"]([^\'"]+)[\'"].*$')
    REGEXP_PARAMETER = re.compile('^(.*?)\{\{(.*?)\}\}(.*)$')

    # TODO: if clauses, for loops - recursion seems a little bit tricky ;-)

    def __init__(self, *args, **kwargs):
        _log('HTTPTemplate __init__')
        self._kwargs = kwargs
        self._kwargs['ts'] = str(time.time())
        # print('self._kwargs', self._kwargs)
        super().__init__(*args, **kwargs)   

    async def _include(self, filename):
        _log('HTTPTemplate _include', filename)
        _file_generator = self._template_file(f'/templates/{filename}' , send_headers=False)
        for _line in _file_generator:
            yield _line

    async def _internal_command(self, file_generator=None, command=None):
        _match = re.match(HTTPTemplate.REGEXP_INCLUDE, command)
        _log('HTTPTemplate _internal_command', command, _match)
        if _match:
            for _line in self._include(_match.group(1).decode()):
                yield _line

    async def _template_file(self, filepath, send_headers=True):
        _log('HTTPTemplate _template_file', filepath)
        _file_generator = self.file(filepath,is_static=False,etag=False,send_headers=send_headers) # TODO: Maybe the _kwargs + filepath?     
        #_log('HTTPTemplate keys', self._kwargs)
        #_log('HTTPTemplate file line by line', filepath) 
        for _line in _file_generator:  
            _match = re.match(HTTPTemplate.REGEXP_COMMAND, _line)
            if _match:
                for _sub_line in self._internal_command(_file_generator, command=_match.group(1)):
                    yield _sub_line
            else:
                while True:
                    _match = re.match(HTTPTemplate.REGEXP_PARAMETER, _line)
                    if not _match:
                        break
                    _log('HTTPTemplate _match', _line , '|', _match.group(2))
                    _pre , _key,  _post = _match.group(1), _match.group(2).decode(), _match.group(3)
                    _log('HTTPTemplate _line', _pre , '|', _key, '|', _post)
                    yield _pre.lstrip()
                    if _key in self._kwargs.keys():
                        if callable(self._kwargs[_key]):                           
                            for _subline in self._kwargs[_key](**self._kwargs):
                                yield _subline
                        else:
                            yield str(self._kwargs[_key])
                    else:
                        print(f"WARN: Template '{filepath}' has no value for key '{_key}'")
                    _line = _post
                if _line != b"\r\n":
                    _line = _line.lstrip()
                yield _line

    async def callback(self, request: Request):
        _log('HTTPTemplate callback')
        if re.match('^/templates/.*$', request.path):
            try:
                for _line in self._template_file(request.path):
                    yield _line
                yield None
            except Exception404:
                yield self.Status404()
            return
            
        for _line in super().callback(request):
            yield _line
