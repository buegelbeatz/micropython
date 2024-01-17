
import uasyncio
import socket
import gc

# TODO: What's about the issue : DNS server error: [Errno 12] ENOMEM

def _log(*data):
    # print('connector.dns', *data)
    pass

class _DNSQuery:
    def __init__(self, data):
        self.data = data
        self.domain = ''
        tipo = (data[2] >> 3) & 15  # Opcode bits
        if tipo == 0:  # Standard query
            ini = 12
            lon = data[ini]
            while lon != 0:
                self.domain += data[ini + 1:ini + lon + 1].decode('utf-8') + '.'
                ini += lon + 1
                lon = data[ini]

    def response(self, ip):
        if self.domain:
            packet = self.data[:2] + b'\x81\x80'
            packet += self.data[4:6] + self.data[4:6] + b'\x00\x00\x00\x00'  # Questions and Answers Counts
            packet += self.data[12:]  # Original Domain Name Question
            packet += b'\xC0\x0C'  # Pointer to domain name
            packet += b'\x00\x01\x00\x01\x00\x00\x00\x3C\x00\x04'  # Response type, ttl and resource data length -> 4 bytes
            packet += bytes(map(int, ip.split('.')))  # 4bytes of IP
        return packet

class DNS:

    def __init__(self, ip=None):
        _log('DNS __init__')
        self.ip = ip
        self._socket = None  
        self._socket_setup()
        uasyncio.create_task(self._loop())     

    def _socket_setup(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setblocking(False)
        self._socket.bind(('0.0.0.0', 53))   
        print('(re)start dns...')

    async def _loop(self):
        while True:
            try:
                gc.collect()
                yield uasyncio.core._io_queue.queue_read(self._socket)
                data, addr = self._socket.recvfrom(256)
                dns = _DNSQuery(data)
                self._socket.sendto(dns.response(self.ip), addr)
                _log('DNS _loop' , dns.domain, self.ip)

            except Exception as e:
                _log("DNS server error:", e)
                await uasyncio.sleep_ms(500)
                self._socket.close()
                await uasyncio.sleep_ms(500)
                self._socket_setup()
            await uasyncio.sleep_ms(250)
