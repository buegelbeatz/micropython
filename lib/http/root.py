from . import cache
from .request import Request

# TODO: Check if order of root -> connect make eventually more sense...

def _log(*data):
    # print('http.root', *data)
    pass

class HTTPRoot(cache.HTTPCache):

    PATH = b'/'

    def __init__(self, *args, **kwargs):
        _log('HTTPRoot __init__')
        self.title = kwargs['title'] if 'title' in kwargs.keys() else 'esp32-unknown'
        super().__init__(*args, title=self.title, **kwargs)
        
    async def callback(self, request: Request):
        _log('HTTPRoot callback')
        if HTTPRoot.PATH == request.path:
            request.path = b'/templates/index.html'
        for _line in super().callback(request):
            yield _line



