import re

from ssdp.ssdp import Ssdp
from ssdp.tools import get_hex, load_from_path, get_mac, format_str
from debugger import Debugger

debug = Debugger(color_schema='green')
debug.active = True

class Belkin(Ssdp):

    TEMLATES_ROOT = "/ssdp/belkin_"
    M_SEARCH_ANSWER = load_from_path(f"{TEMLATES_ROOT}m_search_answer.txt")
    SETUP_ANSWER = load_from_path(f"{TEMLATES_ROOT}setup_answer.xml")
    EVENT_SERVICE_ANSWER = load_from_path(f"{TEMLATES_ROOT}eventservice_answer.xml")
    UPN_CONTROL_BASICEVENT_1_ANSWER = load_from_path(f"{TEMLATES_ROOT}upn_control_basicevent1_answer.xml")
    XML_HEADER = load_from_path(f"{TEMLATES_ROOT}xml_header.txt")
    NLS = "38323636-4558-4dda-9188-cda0e6-{hex_6_4}" # b9200ebb-736d-4b93-bf03-835149d13983

    @debug.show
    def __init__(self, ip=None, tcp_port=None, name=None):
        self.state = 0
        self.action_service_regexp = re.compile(r"^[\s\S]*?<u:([^\s]+)[\s\S]*?xmlns:u=\"([^\"]+)[\s\S]*$") # TODO: ssdp ??
        self.binary_state_regexp = re.compile(r"^[\s\S]*?<BinaryState>\s*(\d)\s*<[\s\S]*$")
        _hex_6_4 = get_hex('hex_6_4', get_mac())
        # TODO serial number: first 6 random digits
        _nls = format_str(Belkin.NLS, **{'hex_6_4':f"{_hex_6_4}"})
        _unique_service_name=f"uuid:Socket-1_0-{_nls}"
        _setup_xml = format_str(Belkin.SETUP_ANSWER, **{'name':name, 'unique_service_name': _unique_service_name})
        Ssdp.__init__(self,
                           m_search_response=format_str(Belkin.M_SEARCH_ANSWER, **{'nls': _nls}),
                           setup_answer=format_str(Belkin.XML_HEADER, **{'length': len(_setup_xml), "date":"{date}"}) + _setup_xml,
                           eventservice_answer=format_str(Belkin.XML_HEADER, **{'length': len(Belkin.EVENT_SERVICE_ANSWER)}) + Belkin.EVENT_SERVICE_ANSWER,
                           ip=ip,
                           tcp_port=tcp_port,
                           # discover_patterns=["ssdp:discover"], # man: input st: output
                           discover_patterns=["urn:Belkin:device:**","upnp:rootdevice","ssdp:all"], # man: input st: output
                           notification_type="urn:Belkin:device:**",
                           unique_service_name=_unique_service_name)

    @debug.show
    @Ssdp.tcpEvent
    def ssdp_request(self,body):
        # TODO: error handling
        _match = self.action_service_regexp.search(body)
        _action, _service = _match.group(1), _match.group(2)
        _match = self.binary_state_regexp.search(body)
        _state = _match.group(1)
        if re.match(r"Set.*",_action):
            self.state = _state
        _answer_xml = format_str(Belkin.UPN_CONTROL_BASICEVENT_1_ANSWER, **{'action':f"{_action}Response", 'state': self.state})
        return format_str(Belkin.XML_HEADER, **{'length': len(_answer_xml), "date":"{date}"}) + _answer_xml
