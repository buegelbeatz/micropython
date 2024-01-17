
import usocket as socket
import uasyncio
import sys

from debugger import Debugger

debug = Debugger(color_schema='blue')
#debug.active = True

class Udp:

    _udp_handler = []

    def _inet_aton(self,addr):
        return bytes(map(int, addr.split('.')))
    
    def items(self):
        return {k:v for (k,v) in self.__dict__.items() if not k.startswith('_')}

    @debug.show
    def __init__(self, ip=None, udp_port=None, udp_ip=None):
        self.ip = ip
        self.udp_port = udp_port
        self.udp_ip = udp_ip
        if not udp_port or not udp_ip:
            debug.error("udp_port and udp_ip needs to have values.")
            sys.exit(0)
        self._udp_receive_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._udp_receive_socket.bind(socket.getaddrinfo("0.0.0.0", self.udp_port, socket.AF_INET, socket.SOCK_DGRAM)[0][4])
        group_address = self._inet_aton(self.udp_ip) + self._inet_aton(self.ip)
        self._udp_receive_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, group_address)
        self._udp_send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        uasyncio.create_task(self._udp_loop())

    @debug.show
    def udpSend(self, message, addr=None):
        try:
            self._udp_send_socket.sendto(message.encode(), addr if addr else (self.udp_ip, self.udp_port))
        except Exception as e:
            debug.error(e)

    @debug.show
    def _trigger_udp_event(self, data, address, alive, byebye):
        if len(Udp._udp_handler) > 0:
             _data = None
             if isinstance(data, bytes):
                _data = data.decode()
             for _handler in Udp._udp_handler:
                  _handler(self,_data, address, alive, byebye)

    @debug.show
    def udpEvent(func):
        Udp._udp_handler.append(func)
        return func
    
    @debug.show
    def __del__(self):
        self._trigger_udp_event(None,None,None,True)
        sys.exit(0)

    async def _udp_loop(self):
        await uasyncio.sleep_ms(1000)
        self._trigger_udp_event(None,None,True,None)
        try:
            while True:
                data, address =  self._udp_receive_socket.recvfrom(2048)
                self._trigger_udp_event(data,address,None,None)
                await uasyncio.sleep_ms(500)
        except KeyboardInterrupt:
            self._trigger_udp_event(None,None,None,True)