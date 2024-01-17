import uasyncio
import time
import re
from .request import Request

def _log(*data):
    print('http.base', *data)
    pass

class Exception404(Exception):
    pass

class HTTPBase:

    def __init__(self, ip="0.0.0.0", port=80, **kwargs):
        _log('HTTPBase __init__', ip, port)
        self.ip = ip
        self.port = port
        uasyncio.create_task(uasyncio.start_server(self._loop, self.ip, self.port))

    async def _send_headers(self, suffix, is_gz=False, etag=None, length=0):
        _log('HTTPBase _send_headers', suffix, is_gz, etag, length)
        if not suffix in Request.CONTENT_TYPE.keys():
            raise Exception404  
        yield b"HTTP/1.1 200 OK\r\n"
        yield f"Content-Type: {Request.CONTENT_TYPE[suffix]}\r\n".encode('utf-8')
        if is_gz:
            yield b"Content-Encoding: gzip\r\n"
        if etag:
            yield f"ETag: W/\"{str(hash(etag))}\"\r\n".encode('utf-8')
        if length:
            yield f"Content-Length: {str(length)}\r\n".encode('utf-8')
        else:
            yield "Connection: close\r\n".encode('utf-8')
        yield b"\r\n"

    def Status404(self):
        return b"HTTP/1.1 404 Not Found\r\n\r\n" 

    async def websocket_callback(self, request, data):  
        _log('HTTPBase websocket_callback')

    async def callback(self, request: Request):
        _log('HTTPBase callback')
        try:
            request.writer.close()
        except:
            pass

    async def _loop(self, reader, writer):
        _request_line = ''
        _answer_line = ''
        _raw_data = await reader.read(Request.BUF_SIZE) # TODO: Only would work for GET, not for POST - ERROR Handling
        _raw_parts = _raw_data.split(b"\r\n\r\n")
        _raw_headers = _raw_parts[0].split(b"\r\n")
        _start = time.time_ns()
        for _raw_header in _raw_headers:
            if not _request_line:
                _request_line = _raw_header
                _log('HTTPBase _loop', _request_line.decode())
                try:
                    method, uri, proto = _request_line.split(b" ")
                except Exception as e:
                    print("Malformed request: {}".format(_request_line))
                    reader.close()
                    return
                _request = Request(method=method, uri=uri, proto=proto, reader=reader, writer=writer)  
            else:
                _match = re.match(Request.HEADER_REGEXP,_raw_header)
                if _match:
                    _key, _value = _match.group(1).decode().lower(), _match.group(2).decode().rstrip()
                    _request.headers[_key] = _value                          

        if _request.method == b"POST":
            _post_buffer = bytearray()
            if _raw_parts[1]:
                _post_buffer = _raw_parts[1]
                if len(_post_buffer) == Request.BUF_SIZE:
                    _post_buffer += await reader.read()
            _request.body = _post_buffer
        _log('request', _request.__dict__)
        try:
            _buffer = bytearray()
            for _line in self.callback(_request):
                _bytes = _line if type(_line) is bytes else _line.encode() if type(_line) is str else b""
                if not _answer_line:
                    _answer_line = _bytes.decode()
                if _bytes == b"":
                    break
                _buffer += _bytes
                if len(_buffer) > Request.BUF_SIZE:
                    writer.write(_buffer)
                    await writer.drain()
                    _buffer = bytearray()
            if len(_buffer):
                writer.write(_buffer)
                await writer.drain()
            _buffer = bytearray()
        except Exception as e:
            _answer_line = str(e)
        writer.close()
        await writer.wait_closed()
        reader.close()
        await reader.wait_closed() 
        _request.performance.append({'send response': time.time_ns() - _start})
        _duration = int((time.time_ns() - _start) >> 20)
        print(f"{_request_line.decode().rstrip()} -[{_duration}ms]-> {_answer_line.rstrip()}")

  