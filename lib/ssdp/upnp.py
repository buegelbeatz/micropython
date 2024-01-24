from ssdp.tools import format_str, headers_to_dict, date
from ssdp.udp import Udp
from debugger import Debugger

debug = Debugger(color_schema='magenta',tab=2)
# debug.active = True

class Upnp(Udp):

    _upnp_handler = []

    UPNP_MCAST_IP = "239.255.255.250"
    UPNP_PORT = 1900

    HEADER_NOTIFY = (
        "NOTIFY * HTTP/1.1",
        f"HOST: {UPNP_MCAST_IP}:{UPNP_PORT}", #UPNP_MCAST_IP, UPNP_PORT
        "CACHE-CONTROL: max-age={cache}",
        "SERVER: {server}", 
        "USN: {usn}", # USN (Unique Service Name) - uuid:550e8400-e29b-11d4-a716-446655440000::urn:schemas-upnp-org:service:ConnectionManager:1
        "NT: {notification_type}", # NT (Notification Type) - urn:schemas-upnp-org:service:ConnectionManager:1
        "NTS: {notification_sub_type}") # NTS (Notification Sub Type) - ssdp:alive, ssdp:byebye 

    @debug.show
    def __init__(self, **kwargs):
        self._upnp_child = kwargs
        Udp.__init__(self, udp_ip=Upnp.UPNP_MCAST_IP, udp_port=Upnp.UPNP_PORT, ip=kwargs['ip'])

    @debug.show
    def upnpSend(self, template=None, address=None, **kwargs):
        if not template:
            _message = format_str("\r\n".join(Upnp.HEADER_NOTIFY), **kwargs, **self._upnp_child, **{'date': date()})
        else:
            _message =  format_str(template, **kwargs, **self._upnp_child, **{'date': date()}).replace("\n","\r\n")
        self.udpSend(_message,address)

    @Udp.udpEvent
    @debug.show
    def _trigger_upnp_event(self, data, address, alive, byebye):
        if len(Upnp._upnp_handler) > 0:
            if data:
                _data = None
                _data = headers_to_dict(data)
                _data['_REFERER'] = {'ip':address[0],'port':address[1]}
                for _handler in Upnp._upnp_handler:
                    _handler(self, alive, byebye, **_data)

    @debug.show
    def upnpEvent(func):
        Upnp._upnp_handler.append(func)
        return func
