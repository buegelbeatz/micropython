import uasyncio
import utime as time

from debugger import Debugger

debug = Debugger(color_schema='yellow',tab=2)
# debug.active = True

class Tcp:

    _tcp_handler = []

    ERROR_404 = """HTTP/1.1 404 Not Found
Content-Type: text/plain; charset=utf-8
Content-Length: 11
Connection: close

Not Found

"""

    @debug.show
    def __init__(self, **kwargs):
        self._tcp_child = kwargs
        _server = uasyncio.start_server(self._request, self._tcp_child['ip'], self._tcp_child['tcp_port'])
        uasyncio.create_task(_server)

    @debug.show
    def _trigger_tcp_event(self, uri, body=None):
        if len(Tcp._tcp_handler) > 0:
            for _handler in Tcp._tcp_handler:
                _answer = _handler(self,uri, body)
                if _answer:
                    return _answer

    @debug.show
    def tcpEvent(func):
        Tcp._tcp_handler.append(func)
        return func

    async def _request(self, reader, writer):
        body = None
        _request_line = await reader.readline()
        method, uri, _ = _request_line.split(b" ")
        if method == b"POST" or method == b"PUT":
            _header_mode = True
            _content_length = 0
            while True:
                _next_line = await reader.readline()
                if not _next_line or _next_line == b'':
                    break
                if _next_line == b"\r\n":
                    _header_mode = False
                if _header_mode:
                    _key, _value = _next_line.decode().strip().split(": ", 1)
                    if _key.lower() == "content-length":
                        _content_length = int(_value)
                if not _header_mode and _content_length:
                    _body = await reader.read(_content_length)
                    if _body:
                        body = _body.decode()
                    break
        _start = time.ticks_ms()
        _answer = self._trigger_tcp_event(uri.decode(), body)
        debug.timer(_start, 'request')
        if _answer is None:
            _answer = Tcp.ERROR_404
        _bytes = _answer if type(_answer) is bytes else _answer.encode() if type(_answer) is str else b""
        writer.write(_bytes)
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        reader.close()
        await reader.wait_closed()
