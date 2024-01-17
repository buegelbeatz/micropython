import uasyncio

from debugger import Debugger

debug = Debugger(color_schema='yellow')
debug.active = True

class Tcp:

    _tcp_handler = []

    BUFFER_SIZE = 2048

    @debug.show
    def __init__(self, ip="0.0.0.0", tcp_port=80):
        self.ip = ip
        self.tcp_port = tcp_port
        uasyncio.create_task(uasyncio.start_server(self._loop, self.ip, self.tcp_port))

    @debug.show
    def _trigger_tcp_event(self, uri, body):
        _answer = None
        if len(Tcp._tcp_handler) > 0:
            for _handler in Tcp._tcp_handler:
                _answer = _handler(self,uri, body)
                if _answer:
                    break
        return _answer

    @debug.show
    def tcpEvent(func):
        Tcp._tcp_handler.append(func)
        return func
    
    async def _loop(self, reader, writer):
        _request_line = ''
        _raw_data = await reader.read(Tcp.BUFFER_SIZE)
        _raw_parts = _raw_data.split(b"\r\n\r\n")
        _raw_headers = _raw_parts[0].split(b"\r\n")
        body = None
        for _raw_header in _raw_headers:
            if not _request_line:
                _request_line = _raw_header
                try:
                    method, uri, _ = _request_line.split(b" ")
                except Exception as e:
                    debug.error(f"Malformed request: {_request_line.decode()}: {e}")
                    reader.close()
                    writer.close()
                    return
        if method == b"POST":
            _post_buffer = bytearray()
            if _raw_parts[1]:
                _post_buffer = _raw_parts[1]
                if len(_post_buffer) == Tcp.BUFFER_SIZE:
                    _post_buffer += await reader.read()
            body = _post_buffer.decode()
        answer = self._trigger_tcp_event(uri.decode(), body)
        try:
            if answer:
                debug.showDict(**{'response':answer})
                writer.write(answer.encode())
        except Exception as e :
            debug.error(e)
        writer.close()
        await writer.wait_closed()
        reader.close()
        await reader.wait_closed() 
