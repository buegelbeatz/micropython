import re
from . import template
from .request import Request

def _log(*data):
    # print('http.cache', *data)
    pass

class HTTPCache(template.HTTPTemplate):

    cache_ids = None
    HEADER_REGEXP = re.compile('^ *W/"([^"]+)" *$')

    def __init__(self, *args, **kwargs):
        _log('HTTPCache __init__')
        HTTPCache.cache_ids = {}
        super().__init__(*args, **kwargs)

    def Status304(self):
        return b"HTTP/1.1 304 Not Modified\r\n\r\n"

    async def callback(self, request: Request):
        _log('HTTPCache callback')
        if "if-none-match" in request.headers.keys():
            if not request.path in HTTPCache.cache_ids.keys():
                stat, _, _ = self.file_statistic(request.path)
                HTTPCache.cache_ids[request.path] = str(hash(stat))
            _match = re.match(HTTPCache.HEADER_REGEXP, request.headers['if-none-match'])
            if HTTPCache.cache_ids[request.path] == _match.group(1):
                yield self.Status304()
                return
        for _line in super().callback(request):
            yield _line
