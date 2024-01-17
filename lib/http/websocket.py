from . import root
from .request import Request
import time
import json
import uasyncio
import uhashlib, ubinascii
import websocket

# TODO: splitting a WebsocketRequest class

def _wraps(f):
    return lambda f:f

def _log(*data):
    # print('http.websocket', *data)
    pass

def websocketReceive():
    def decorate_websocket_receive(func):
        @_wraps(func)
        def wrap_websocket_receive(request, data):
            return func(request, data)
        HTTPWebsocket._websocket_handle.append(wrap_websocket_receive)
        return wrap_websocket_receive
    return decorate_websocket_receive

def websocketOpened():
    def decorate_websocket_opened(func):
        @_wraps(func)
        def wrap_websocket_opened(request):
            return func(request)
        HTTPWebsocket._websocket_opened.append(wrap_websocket_opened)
        return wrap_websocket_opened
    return decorate_websocket_opened

def websocketClosed():
    def decorate_websocket_closed(func):
        @_wraps(func)
        def wrap_websocket_closed(request):
            return func(request)
        HTTPWebsocket._websocket_closed.append(wrap_websocket_closed)
        return wrap_websocket_closed
    return decorate_websocket_closed

class WSWriter:

    def __init__(self, request):
        self.s = request.writer

    async def awrite(self, data):
        assert len(data) < 126
        await self.s.awrite(b"\x81")
        await self.s.awrite(bytes([len(data)]))
        await self.s.awrite(data)

    async def send(self, data):
        _log('WSWriter send', data, dir(self))
        await self.awrite(json.dumps(data).encode())

class HTTPWebsocket(root.HTTPRoot):

    CONT = 0
    TEXT = 1
    BINARY = 2
    CLOSE = 8
    PING = 9
    PONG = 10

    _websocket_handle = []
    _websocket_opened = []
    _websocket_closed = []

    #_requests = {}

    PATH = b'/ws'
    DELAY_MS = 100

    def __init__(self, *args, **kwargs):
        _log('HTTPWebsocket __init__')
        super().__init__(*args, **kwargs)

    def _cleanup(self, request):
        _log('HTTPWebsocket _cleanup', request)
        if request.writer:
            for _handle in HTTPWebsocket._websocket_closed:
                _handle(request)
        try:
            request.reader.s.close()
        except:
            pass
        try:
            request.reader.close()
        except:
            pass
        request.writer = None 
        request.reader = None
        request._send_buffer = []


    def Status400(self):
        return b"HTTP/1.1 400 Bad Request\r\n\r\n"

    def _parse_frame_header(self, header):
        _log('HTTPWebsocket _parse_frame_header', header)
        fin = header[0] & 0x80
        opcode = header[0] & 0x0f
        if fin == 0 or opcode == self.CONT:  # pragma: no cover
            raise Exception('Continuation frames not supported')
        has_mask = header[1] & 0x80
        length = header[1] & 0x7f
        if length == 126:
            length = -2
        elif length == 127:
            length = -8
        return fin, opcode, has_mask, length

    async def _read_frame(self, request):
        header = await request.reader.read(2)
        _log('HTTPWebsocket _read_frame', header)
        if not header or len(header) != 2:  # pragma: no cover
            raise Exception('Websocket connection closed')
        fin, opcode, has_mask, length = self._parse_frame_header(header)
        if length == -2:
            length = await request.reader.read(2)
            length = int.from_bytes(length, 'big')
        elif length == -8:
            length = await request.reader.read(8)
            length = int.from_bytes(length, 'big')
        if has_mask:  # pragma: no cover
            mask = await request.reader.read(4)
        payload = await request.reader.read(length)
        if has_mask:  # pragma: no cover
            payload = bytes(x ^ mask[i % 4] for i, x in enumerate(payload))
        return opcode, payload

    def _process_websocket_frame(self, opcode, payload):
        _log('HTTPWebsocket _process_websocket_frame', opcode, payload)
        if opcode == self.TEXT:
            payload = payload.decode()
        elif opcode == self.BINARY:
            pass
        elif opcode == self.CLOSE:
            raise Exception('Websocket connection closed')
        elif opcode == self.PING:
            return self.PONG, payload
        elif opcode == self.PONG:  # pragma: no branch
            return None, None
        return None, payload

    async def _websocket_loop(self,request: Request):
        _log('_websocket_loop')
        try:
            _task_receive = uasyncio.create_task(self._receive_loop(request))
            _task_send = uasyncio.create_task(self._send_loop(request))
            while True: 
                if request.reader is None or request.writer is None:
                    break
                await uasyncio.sleep(5)
        except Exception as e:
            print('_websocket_loop error', e)
        self._cleanup(request)
        try:
            _task_receive.cancel()
            _task_send.cancel()
            await uasyncio.sleep(0)
            uasyncio.current_task().cancel()
            await uasyncio.sleep(0)
        except:
            pass
        
        _log('_websocket_loop close')

    async def _send_loop(self, request):
        _log('_send_loop')
        try:
            while True:
                if request.reader is None or request.writer is None:
                    break
                if len(request._send_buffer):
                    _data = request._send_buffer.pop(0)
                    await request.writer.awrite(json.dumps(_data['data']).encode())
                    _delay_ms = int((time.time_ns() - _data['ts']) >> 20)
                    print(f"{HTTPWebsocket.PATH.decode()} -*-[{_delay_ms}ms]-> {_data['data']}")
                await uasyncio.sleep_ms(HTTPWebsocket.DELAY_MS)
        except Exception as e:
            print('_send_loop error', e)
        self._cleanup(request)
        _log('_send_loop close')

    async def _receive_loop(self, request):
        _log('_receive_loop')
        try:
            while True: 
                if request.reader is None or request.writer is None:
                    break
                opcode, payload = await self._read_frame(request)
                send_opcode, data = self._process_websocket_frame(opcode, payload)
                if send_opcode and data and request.writer:
                    await request.writer.awrite(data)
                    await uasyncio.sleep_ms(HTTPWebsocket.DELAY_MS)
                    continue
                if data is not None:
                    _json = json.loads(data)
                    for _handle in HTTPWebsocket._websocket_handle:
                        _handle(request, _json)
                        await uasyncio.sleep(0)
                    await super().websocket_callback(request, _json)
                await uasyncio.sleep_ms(HTTPWebsocket.DELAY_MS)
        except Exception as e:
                print('receive error', e)
        self._cleanup(request)
        _log('_receive_loop close')

    def _make_respkey(self, webkey):
        d = uhashlib.sha1(webkey)
        d.update(b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11")
        return ubinascii.b2a_base64(d.digest())[:-1]

    async def _awrite(self, data):
        assert len(data) < 126
        await self.awrite(b"\x81")
        await self.awrite(bytes([len(data)]))
        await self.awrite(data)

    def _send_upgrade(self, respkey):             
        yield b"HTTP/1.1 101 Switching Protocols\r\n"
        yield b"Upgrade: websocket\r\n"
        yield b"Connection: Upgrade\r\n"
        yield f"Sec-WebSocket-Accept: {respkey}\r\n\r\n".encode()

    async def _init(self, request: Request):
        _log('HTTPWebsocket _init')
        webkey = request.headers['sec-websocket-key'] if 'sec-websocket-key' in request.headers.keys() else None
        if not webkey or \
            'connection' not in request.headers.keys() or \
            'upgrade' not in request.headers.keys() or \
            request.headers['connection'].lower() != 'upgrade' or \
            request.headers['upgrade'].lower() != 'websocket':
            yield self.Status400()
            return
        respkey = self._make_respkey(webkey)
        if not respkey:
            yield self.Status400()
            return  
        for _line in self._send_upgrade(respkey.decode()):
            yield _line      
        ws = websocket.websocket(request.reader.s)
        request.reader = uasyncio.StreamReader(request.reader.s, ws)  
        request.writer = WSWriter(request)
        # request.send = lambda data:await request.writer.awrite(json.dumps({'data': data, 'ts': time.time_ns()}).encode())
        request.key = respkey
        for _handle in HTTPWebsocket._websocket_opened:
            _handle(request)
        uasyncio.create_task(self._websocket_loop(request))

    async def callback(self, request: Request):
        _log('HTTPWebsocket callback')
        if request.path == HTTPWebsocket.PATH:
            try:
                for _line in self._init(request):
                    yield _line
            except Exception as e:
                print('HTTPWebsocket callback error', e) #### stream operation not supported
                self._cleanup(request)
            _log('HTTPWebsocket callback done')
            return 
        for _line in super().callback(request):
            yield _line