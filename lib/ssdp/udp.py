
import usocket as socket
import uasyncio
import sys
import ubinascii

from ssdp.base import Base

from debugger import Debugger
import error

debug = Debugger(color_schema='blue',tab=3)
#debug.active = True

class Udp(Base):

    UDP_MESSAGE_FREQUENCY_MS = 3000
    UDP_LOOP_DELAY_MS = 500
    UDP_BUFFER_SIZE_BYTES = 1024

    _udp_handler = []

    def inet_aton(self,addr):
        return bytes(map(int, addr.split('.')))

    @debug.show
    def __init__(self, udp_port=1900, udp_ip="239.255.255.250", ip=None):
        Base.__init__(self)
        self.stopped = False
        self.broadcast_address = (udp_ip, udp_port)
        self._udp_receive_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._udp_receive_socket.bind(socket.getaddrinfo("0.0.0.0", udp_port, socket.AF_INET, socket.SOCK_DGRAM)[0][4])
        self._udp_receive_socket.setblocking(False)
        _group_address = self.inet_aton(udp_ip) + self.inet_aton(ip)
        self._udp_receive_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, _group_address)
        self._udp_send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        uasyncio.create_task(self._udp_loop())

    @error.exception
    @debug.show
    def udpSend(self, message, addr=None):
        """Sending data to the network"""
        self._udp_send_socket.sendto(message.encode(), addr if addr else self.broadcast_address)

    @debug.show
    def _trigger_udp_event(self, data, address, alive, byebye):
        """Sending incoming data to the registered callbacks"""
        if len(Udp._udp_handler) > 0:
             for _handler in Udp._udp_handler:
                  _handler(self,data if type(data) is not bytes else data.decode(), address, alive, byebye)

    @debug.show
    def udpEvent(func):
        """Adding upnp handler via decorator to this instance"""
        Udp._udp_handler.append(func)
        return func
    
    @debug.show
    def __del__(self):
        """If program ends f.e. because of keyboard interrupt, try to send a bye to the rest of the world."""
        self._trigger_udp_event(None,None,None,True)
        sys.exit(0)

    async def _udp_loop(self):
        """Receiving udp messages and deligate them to the surrounding upnp instance"""
        await uasyncio.sleep_ms(Udp.UDP_LOOP_DELAY_MS)
        self._trigger_udp_event(None,None,True,None)
        try:
            while True:
                if self.stopped:
                    break
                await uasyncio.sleep_ms(Udp.UDP_LOOP_DELAY_MS)
                data, address = None, None
                try:
                    data, address =  self._udp_receive_socket.recvfrom(Udp.UDP_BUFFER_SIZE_BYTES)
                except Exception as e:
                    pass

                if data:
                    if not self.request_frequence_check(data, Udp.UDP_MESSAGE_FREQUENCY_MS):
                        self._trigger_udp_event(data,address,None,None)
                
        except KeyboardInterrupt:
            self._trigger_udp_event(None,None,None,True)