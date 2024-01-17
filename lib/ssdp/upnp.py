from ssdp.tools import format_str, headers_to_dict
from ssdp.udp import Udp
from debugger import Debugger

debug = Debugger(color_schema='magenta')
# debug.active = True

class Upnp(Udp):

    _upnp_handler = []

    UPNP_MCAST_IP = "239.255.255.250"
    UPNP_PORT = 1900

    UPNP_SERVER = "Unspecified, UPnP/1.0, Unspecified"
    UPNP_USER_AGENT = "redsonic"
    UPNP_CHACHE_TIME = 86400

    HEADER_NOTIFY = (
        "NOTIFY * HTTP/1.1",
        f"HOST: {UPNP_MCAST_IP}:{UPNP_PORT}", #UPNP_MCAST_IP, UPNP_PORT
        f"CACHE-CONTROL: max-age={UPNP_CHACHE_TIME}",
        f"SERVER: {UPNP_SERVER}", 
        "USN: {unique_service_name}", # USN (Unique Service Name) - uuid:550e8400-e29b-11d4-a716-446655440000::urn:schemas-upnp-org:service:ConnectionManager:1
        "NT: {notification_type}", # NT (Notification Type) - urn:schemas-upnp-org:service:ConnectionManager:1
        "NTS: {notification_sub_type}") # NTS (Notification Sub Type) - ssdp:alive, ssdp:byebye 

    @debug.show
    def __init__(self, ip="0.0.0.0", unique_service_name=None, notification_type=None):
        Udp.__init__(self, ip=ip, udp_port=Upnp.UPNP_PORT, udp_ip=Upnp.UPNP_MCAST_IP)
        self.ip = ip
        self.cache = Upnp.UPNP_CHACHE_TIME
        self.server = Upnp.UPNP_SERVER
        self.user_agent = Upnp.UPNP_USER_AGENT
        self.unique_service_name = unique_service_name
        self.notification_type = notification_type

    @debug.show
    def upnpSend(self, template=None, address=None, **kwargs):
        #try:
        if not template:
            _message = format_str("\r\n".join(Upnp.HEADER_NOTIFY),**self.items())
        else:
            _message =  format_str(template, **kwargs).replace("\n","\r\n")
        self.udpSend(_message,address)
        #except Exception as e:
        #    debug.error(e)

    @debug.show
    @Udp.udpEvent
    def _trigger_upnp_event(self, data, address, alive, byebye):
        if len(Upnp._upnp_handler) > 0:
            _data = None
            if data:
                _data = headers_to_dict(data)
                _data['_REFERER'] = {'ip':address[0],'port':address[1]}
                for _handler in Upnp._upnp_handler:
                    _handler(self, _data, alive, byebye)

    @debug.show
    def upnpEvent(func):
        Upnp._upnp_handler.append(func)
        return func