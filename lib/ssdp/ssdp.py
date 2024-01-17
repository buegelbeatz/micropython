import re

from ssdp.upnp import Upnp
from ssdp.tcp import Tcp
from ssdp.tools import wrapper, date, format_str
from debugger import Debugger

debug = Debugger(color_schema='cyan')
debug.active = True

class Ssdp(Tcp,Upnp):

    _tcp_handler = []

    SSDP_DISCOVER = 'ssdp:discover'

    @debug.show
    def __init__(self,**kwargs):
        self.discover_patterns = kwargs['discover_patterns']
        self.m_search_response = kwargs['m_search_response']
        self.setup_answer = kwargs['setup_answer']
        self.eventservice_answer = kwargs['eventservice_answer']
        Tcp.__init__(self, kwargs['ip'], kwargs['tcp_port'])
        Upnp.__init__(self, kwargs['ip'], kwargs['notification_type'], kwargs['unique_service_name'])

    @debug.show
    def _ssdpSend(self, **data):
        _params = super(Upnp,self).items() #Upnp.items(self)
        _params['date'] = date()
        _params['st'] = data['st']
        _message = format_str(self.m_search_response, **_params)
        Upnp.upnpSend(self, template=_message, address=(data['_REFERER']['ip'],data['_REFERER']['port']))

    @debug.show
    @Upnp.upnpEvent
    def _trigger_ssdp_event(self, data, alive, byebye):
        if alive:
            Upnp.upnpSend(None,notification_sub_type='ssdp:alive')
        if byebye:
            Upnp.upnpSend(None,notification_sub_type='ssdp:byebye')
        if data:
            if data['_CMD'] == 'M-SEARCH * HTTP/1.1' and data['man'] and data['st']:
                _discover = '|'.join(self.discover_patterns).replace("*",r"\*")
                _pattern = f"^.*({_discover}).*$"
                if re.match(f"^.*({Ssdp.SSDP_DISCOVER}).*$", data['man']) and re.match(_pattern, data['st']):
                    self._ssdpSend(**data)

    @debug.show
    @Tcp.tcpEvent
    def _trigger_ssdp_tcp_event(self, uri, body):
        _answer = None
        if re.match(r"^.*setup\.xml$",uri):
            _answer = self.setup_answer
        if re.match(r"^.*eventservice\.xml$",uri):
            _answer = self.eventservice_answer
        if body:
            for _handler in Ssdp._tcp_handler:
                _answer = _handler(self, body)
                if _answer:
                    break
        return format_str(_answer, **{
            "date": date(),
            'user_agent': Upnp.UPNP_USER_AGENT,
            'server': Upnp.UPNP_SERVER})

    @debug.show
    def tcpEvent(func):
        Ssdp._tcp_handler.append(func)
        return func
