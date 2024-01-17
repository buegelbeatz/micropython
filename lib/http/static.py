import re
import os
import gc
import time
from .base import Exception404, HTTPBase
from .request import Request

def _log(*data):
    # print('http.static', *data)
    pass

class HTTPStatic(HTTPBase):

    def __init__(self, *args, **kwargs):
        _log('HTTPStatic __init__')
        super().__init__(*args, **kwargs)

    def file_statistic(self, filepath):
        _log('HTTPStatic file_statistic', filepath)
        try:
            _gz = '.gz' if not re.match('^.*\.gz$',filepath) else ''
            _filepath = filepath + _gz
            _log('HTTPStatic file_statistic check ', _filepath)
            stat = os.stat(_filepath)
            if stat:
                return stat, _filepath, True
        except:
            pass
        try:
            _log('HTTPStatic file_statistic check ', filepath)
            stat = os.stat(filepath)
            if stat:
                return stat, filepath, False
        except:
            pass
        _log('HTTPStatic file_statistic we should not be here ')
        return None, filepath, False


    async def file(self, filepath, is_static=True, etag=True, send_headers=True, method=b'GET'):
        _file_path_str = filepath if type(filepath) is str else filepath.decode()
        _log('HTTPStatic file', _file_path_str)
        try:
            _ = _file_path_str.index('..')
            print(f"'..' not allowed in path '{_file_path_str}'")
            raise Exception404
        except ValueError:
            pass
        _match = re.match(Request.SUFFIX_REGEXP, _file_path_str)
        _suffix, _is_gz = _match.group(1), _match.group(2)
        if not _suffix in Request.CONTENT_TYPE.keys():
            raise Exception404
        stat, _filepath, _is_gz = self.file_statistic(_file_path_str)         
        if not stat:
            _log(f"'{filepath}[.gz]' not found")
            raise Exception404
        if send_headers:
            _etag = stat if etag is True else etag
            _length = stat[6] if is_static else 0
            for _header in self._send_headers(suffix=_suffix,is_gz=_is_gz,length=_length,etag=_etag):
                _log(_header)
                yield _header
        if method == b'HEAD': # TODO: HEAD /connect HTTP/1.1 -[230ms]-> [Errno 104] ECONNRESET - Maybe related to templating and empty ??
            return
        _log('HTTPStatic open file now', _filepath)
        with open(_filepath) as f:
            gc.collect()
            buf = bytearray(min(stat[6], Request.BUF_SIZE)) if is_static else ''
            try:
                while True:
                    if is_static:
                        size = f.readinto(buf)  
                    else:                    
                        buf,size = f.readline().encode(),1
                    if not buf or size == 0:
                        break
                    yield bytes(buf)
                    # TODO: Pause ?
            except Exception as e:
                print(e)  
        _log('HTTPStatic file done', _filepath)
        
    async def callback(self, request: Request):
        _start = time.time_ns()
        _log('HTTPStatic callback')
        if re.match('^/favicon\.ico$', request.path):
            request.path = b"/static/favicon.ico"
        if re.match('^/static/.*$', request.path):
            try:
                for _line in self.file(request.path,method=request.method):
                    yield _line
            except Exception404:
                yield self.Status404()
            return
        for _line in super().callback(request):
            yield _line
        request.performance.append({'static callback': time.time_ns() - _start})
