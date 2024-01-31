import re
import json
import ubinascii
import uhashlib as hashlib

from ssdp.ssdp import Ssdp
from alexa.hue_devices import HueDevice, HueDeviceType, HueDevices, hue_sat_to_rgb, rgb_to_hue_sat
from ssdp.tools import get_hex, load_from_path, get_mac, format_str, dict_exclude, date
from debugger import Debugger
import error

debug = Debugger(color_schema='green')
# debug.active = True

class Hue(Ssdp):

    _hue_tcp_handler = []

    TEMLATES_ROOT = "/ssdp/hue_"
    M_SEARCH_ANSWER = f"{TEMLATES_ROOT}m_search_answer.txt" # ip, tcp_port, mac, server, cache, udn
    SETUP_ANSWER = f"{TEMLATES_ROOT}setup_answer.xml" # ip, tcp_port, mac, udn
    XML_HEADER = f"{TEMLATES_ROOT}xml_header.txt"
    JSON_HEADER = f"{TEMLATES_ROOT}json_header.txt"
    SERVER = "FreeRTOS/6.0.5, UPnP/1.0, IpBridge/1.17.0"
    CACHE_TIME = 100
    NLS = f"2f402f80-da50-11e1-9b23-cda0e6-{get_hex('hex_6_4', get_mac())}" # b9200ebb-736d-4b93-bf03-835149d13983
    SERVICE = "urn:schemas-upnp-org:device:basic:1"
    UDN = f"uuid:{NLS}"
    LIGHTS_PATTERN_REGEXP = r"/api/([a-f\d]+)/lights(/(\d+)(/([^/]+))?)?$"
    LIGHTS_PATTERN_REGEXP_USER = 1
    LIGHTS_PATTERN_REGEXP_LIGHT = 3
    LIGHTS_PATTERN_REGEXP_STATE = 5

    @debug.show
    def __init__(self, ip=None, tcp_port=None):
        self.devices = HueDevices()
        _hash = hashlib.md5('username' + get_mac())
        self.user_name = ubinascii.hexlify(_hash.digest()).decode()
        self.json_header = load_from_path(Hue.JSON_HEADER).replace('\n', '\r\n')
        self.lights_pattern_regexp = re.compile(Hue.LIGHTS_PATTERN_REGEXP)
        Ssdp.__init__(self,
                        m_search_response=Hue.M_SEARCH_ANSWER,
                        nls=Hue.NLS,
                        udn=Hue.UDN,
                        setup_answer=Hue.SETUP_ANSWER,
                        xml_header=Hue.XML_HEADER,
                        setup_path_pattern=r"^.*description\.xml$",
                        ip=ip,
                        tcp_port=tcp_port,
                        server=Hue.SERVER,
                        service=Hue.SERVICE,
                        cache=Hue.CACHE_TIME,
                        discover_patterns=["device:basic:1","upnp:rootdevice","ssdp:all"], # man: input st: output
                        notification_type="urn:schemas-upnp-org:device:**")
        self._trigger_hue_event(None,'setUpnp',True)

    @debug.show
    def hueEvent(self,func):
        Hue._hue_tcp_handler.append(func)
        return func

    @debug.show
    def _trigger_hue_event(self, name, type, payload=None):
        if len(Hue._hue_tcp_handler) > 0:
            for _handler in Hue._hue_tcp_handler:
                _answer = _handler(name, type, payload) # NO self here, decorator live outside of class hierachy
                if _answer:
                    return _answer
    
    @Ssdp.ssdpEvent
    @debug.show
    def ssdp_request(self,uri, body):
        """https://github.com/bwssytems/ha-bridge/blob/master/README.md"""
        if not uri and body:
            _body = body if type(body) is not str else json.load(body)
            if 'upnp' in _body:
                self._trigger_hue_event(None,'setUpnp',_body['upnp'])
                return
        _payload = None
        _match = self.lights_pattern_regexp.search(uri)
        if _match: # something related to lights
            _user = _match.group(Hue.LIGHTS_PATTERN_REGEXP_USER)
            _light = _match.group(Hue.LIGHTS_PATTERN_REGEXP_LIGHT)
            _state = _match.group(Hue.LIGHTS_PATTERN_REGEXP_STATE)

            if _user and _user == self.user_name:
                _device = None
                if _light:
                    _device = self.devices.get(_light)
                if not _state:
                    if not _device and not _light:
                        #self._trigger_hue_event([ _d.name for _d in self.devices._devices],'getState',None)
                        _payload = self.devices.get_all()
                    if _device:
                        # _answer = self._trigger_hue_event(_device.name,'getState',None) # TODO: Not implemented yet
                        _payload = _device.json()
                if _state == 'state' and body and _device:
                    _body = json.loads(body)
                    if 'on' in _body:
                        if _body['on'] and ('bri' not in _body or not _body['bri']):
                            _body['bri'] = 100
                        if not 'hue' in _body and not 'ct' in _body:
                            _body['red'] = 128
                            _body['green'] = 128
                            _body['blue'] = 128
                    if 'ct' in _body:
                        _body['colormode'] = 'ct'
                    if 'hue' in _body and 'sat' in _body:
                        _body['colormode'] = 'hs'
                        red, green, blue = hue_sat_to_rgb(_body['hue'],_body['sat'])
                        _body['red'] = red
                        _body['green'] = green
                        _body['blue'] = blue
                    
                    _answer = self._trigger_hue_event(_device.name,'setState',_body) 
                    if _answer and type(_answer) is dict and 'red' in _answer and 'green' in _answer and 'blue' in _answer:
                        hue, sat = rgb_to_hue_sat(_answer['hue'],_answer['sat'])
                        _answer['hue'] = hue
                        _answer['sat'] = sat
                        _body.update(_answer)
                    # TODO: Not implemented yet
                    _payload = []
                    for _key, _value in _body.items():
                        if _key in dir(_device):
                            setattr(_device,_key,_value)
                            _payload.append({"success":{f"/lights/{_light}/state/{_key}":_value}})
                    print(json.dumps(_payload))
        if uri == '/api' and body and re.match(r"^.*devicetype.*$",body): # TODO: Somehow directly check in _body
            _payload = [{"success":{"username": self.user_name}}]
        if _payload:            
            _json_string = json.dumps(_payload)
            return format_str(self.json_header, **{'length': (len(_json_string) + 2), 'date': date()}) + _json_string + "\r\n"
        print(uri, body)
