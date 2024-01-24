import re

from ssdp.ssdp import Ssdp
from ssdp.tools import get_hex, load_from_path, get_mac, format_str, date
from debugger import Debugger

debug = Debugger(color_schema='green')
debug.active = True

class Belkin(Ssdp):

    TEMLATES_ROOT = "/ssdp/belkin_"
    M_SEARCH_ANSWER = f"{TEMLATES_ROOT}m_search_answer.txt"
    SETUP_ANSWER = f"{TEMLATES_ROOT}setup_answer.xml"
    EVENT_SERVICE_ANSWER = f"{TEMLATES_ROOT}eventservice_answer.xml"
    UPN_CONTROL_BASICEVENT_1_ANSWER = f"{TEMLATES_ROOT}upn_control_basicevent1_answer.xml"
    XML_HEADER = f"{TEMLATES_ROOT}xml_header.txt"
    SERVER = "Unspecified, UPnP/1.0, Unspecified"
    USER_AGENT = "redsonic"
    CACHE_TIME = 86400
    NLS = f"38323636-4558-4dda-9188-cda0e6-{get_hex('hex_6_4', get_mac())}" # b9200ebb-736d-4b93-bf03-835149d13983
    # UNIQUE_SERVICE_NAME = f"uuid:Socket-1_0-{NLS}"
    SERVICE = "urn:Belkin:service:basicevent:1"
    UDN = f"uuid:Socket-1_0-{NLS}"

    @debug.show
    def __init__(self, ip=None, tcp_port=49000, name=None):
        self.state = 0
        self.action_service_regexp = re.compile(r"^[\s\S]*?<u:([^\s]+)[\s\S]*?xmlns:u=\"([^\"]+)[\s\S]*$") # TODO: ssdp ??
        self.binary_state_regexp = re.compile(r"^[\s\S]*?<BinaryState>\s*(\d)\s*<[\s\S]*$")
        self.upn_control_basicevent_1_answer = load_from_path(Belkin.UPN_CONTROL_BASICEVENT_1_ANSWER).replace('\n', '\r\n')
        Ssdp.__init__(self,
                           m_search_response=Belkin.M_SEARCH_ANSWER,
                           nls=Belkin.NLS,
                           udn=Belkin.UDN,
                           name=name,
                           setup_answer=Belkin.SETUP_ANSWER,
                           xml_header=Belkin.XML_HEADER,
                           setup_path_pattern=r"^.*setup\.xml$",
                           #eventservice_answer=Belkin.EVENT_SERVICE_ANSWER,
                           #event_path_pattern=r"^.*eventservice\.xml$",
                           ip=ip,
                           tcp_port=tcp_port,
                           user_agent= Belkin.USER_AGENT,
                           server=Belkin.SERVER,
                           service=Belkin.SERVICE,
                           cache=Belkin.CACHE_TIME,
                           discover_patterns=["urn:Belkin:device:**","upnp:rootdevice","ssdp:all"], # man: input st: output
                           notification_type="urn:Belkin:device:**")
        _eventservice_answer = load_from_path(Belkin.EVENT_SERVICE_ANSWER).replace('\n', '\r\n')
        self.eventservice_answer = format_str(self.xml_header, **{'length': len(_eventservice_answer)}) + _eventservice_answer

    
    @Ssdp.tcpEvent
    @debug.show
    def ssdp_request(self, uri, body):
        # TODO: error handling
        if re.match(r"^.*eventservice\.xml$",uri):
            return self.eventservice_answer
        _match = self.action_service_regexp.search(body)
        _action, _service = _match.group(1), _match.group(2)
        _match = self.binary_state_regexp.search(body)
        _state = _match.group(1)
        if re.match(r"Set.*",_action):
            self.state = _state
        _payload = {'action':f"{_action}Response", 'state': self.state, 'service': Belkin.SERVICE}
        _answer_xml = format_str(self.upn_control_basicevent_1_answer, **_payload).replace('\r\n', '')
        _payload = {'length': len(_answer_xml), "date":date()}
        _xmlheader_body = self.xml_header + _answer_xml
        return format_str(_xmlheader_body, **_payload, **self._ssdp_child)
