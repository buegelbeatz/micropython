
import time
import re

class Request:

    BUF_SIZE = 2048

    HEADER_REGEXP = re.compile("^\s*(\S+)\s*:\s*(.+?)[\r\n]*$")

    SUFFIX_REGEXP = re.compile('^.*?\.(js|css|html|ico|png|xml|json)(\.gz|)$')

    CONTENT_TYPE = {
        'js': 'text/javascript',
        'css': 'text/css',
        'html': 'text/html',
        'ico': 'image/x-icon',
        'png': 'image/png',
        'xml': 'application/xml',
        'json': 'application/json'
    }

    REQ_RE = re.compile(
        br'^(([^:/\\?#]+):)?' +  # scheme                # NOQA
        br'(//([^/\\?#]*))?' +   # user:pass@hostport    # NOQA
        br'([^\\?#]*)' +         # route                 # NOQA
        br'(\\?([^#]*))?' +      # query                 # NOQA
        br'(#(.*))?')            # fragment              # NOQA

    def __init__(self, method=b'GET', uri='', proto='', reader=None, writer=None, body=None):
        self.uri_parts = re.match(Request.REQ_RE, uri)
        self.method = method
        self.uri = uri
        self.reader = reader
        self.writer = writer
        self._send_buffer = []
        self.performance = []
        self.path = self.uri_parts.group(5) if self.uri_parts else "/"
        self.proto = proto
        self.headers = {}
        self.body = body

    def send(self, data): # TODO: move to WebsocketRequest
        self._send_buffer.append({'ts': time.time_ns(), 'data': data})