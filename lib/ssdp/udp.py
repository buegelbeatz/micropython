
import usocket as socket
import uasyncio
import sys
import ubinascii
import utime as time
import uhashlib as hashlib

from debugger import Debugger
import error

debug = Debugger(color_schema='blue',tab=3)
debug.active = True

class Udp:

    UDP_MESSAGE_FREQUENCY_MS = 3000
    UDP_LOOP_DELAY_MS = 1000
    UDP_BUFFER_SIZE_BYTES = 512

    _udp_handler = []

    def _inet_aton(self,addr):
        return bytes(map(int, addr.split('.')))

    @debug.show
    def __init__(self, **kwargs):
        self._upd_child = kwargs
        self._udp_receive_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._udp_receive_socket.bind(socket.getaddrinfo("0.0.0.0", self._upd_child['udp_port'], socket.AF_INET, socket.SOCK_DGRAM)[0][4])
        self._udp_receive_socket.setblocking(False)
        group_address = self._inet_aton(self._upd_child['udp_ip']) + self._inet_aton(self._upd_child['ip'])
        self._udp_receive_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, group_address)
        self._udp_send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        uasyncio.create_task(self._udp_loop())

    @error.exception
    @debug.show
    def udpSend(self, message, addr=None):
        """Sending data to the network"""
        self._udp_send_socket.sendto(message.encode(), addr if addr else (self._upd_child['udp_ip'], self._upd_child['udp_port']))

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
        _received = {}
        self._trigger_udp_event(None,None,True,None)
        try:
            while True:
                await uasyncio.sleep_ms(Udp.UDP_LOOP_DELAY_MS)
                data = b''
                address = None
                try:
                    data, address =  self._udp_receive_socket.recvfrom(Udp.UDP_BUFFER_SIZE_BYTES)
                except OSError as e:
                    if e.args[0] != 11:  # Ignore EAGAIN error (no data available)
                        raise

                # Take care, that the exactly same broadcast is not evaluated to often in a high frequency
                if data:
                    _hash = hashlib.md5(data)
                    _key = ubinascii.hexlify(_hash.digest()).decode()
                    _time = time.ticks_ms()
                    if _key in _received:
                        if _time - _received[_key] < Udp.UDP_MESSAGE_FREQUENCY_MS:
                            _received[_key] = _time
                            debug.log('.',end='')
                            continue
                        else:
                            del(_received[_key])
                    else:
                        _received[_key] = _time

                    # Deligate the incoming data to upnp
                    self._trigger_udp_event(data,address,None,None)
                
        except KeyboardInterrupt:
            self._trigger_udp_event(None,None,None,True)