import re
import utime as time

from ssdp.upnp import Upnp
from ssdp.tcp import Tcp
from ssdp.tools import wrapper, date, format_str, dict_exclude, dict_include, load_from_path, get_mac
from debugger import Debugger

debug = Debugger(color_schema='cyan',tab=1)
# debug.active = True

class Ssdp(Tcp,Upnp):

    _ssdp_tcp_handler = []

    SSDP_DISCOVER = 'ssdp:discover'
    SSDP_BYEBYE = 'ssdp:byebye'
    SSDP_ALIVE = 'ssdp:alive'
    SSDP_SEARCH_HEADER = 'M-SEARCH * HTTP/1.1'
    SSDP_UPNP_RUNNING_TIME_MS = 120000

    @debug.show
    def __init__(self, **kwargs): # nls, service
        self.initialized_ts = time.ticks_ms()
        self._ssdp_child = dict_include('setup_path_pattern', 'user_agent', 'server', 'discover_patterns',  **kwargs)
        Tcp.__init__(self, **dict_include('ip', 'tcp_port', **kwargs))
        Upnp.__init__(self, **dict_include('ip', 'tcp_port', 'cache', 'server', 'notification_type', 'notification_sub_type', **kwargs))
        self.m_search_response = format_str(load_from_path(kwargs['m_search_response']), **dict_include('nls', 'service', 'udn',  **kwargs))
        self.xml_header = load_from_path(kwargs['xml_header']).replace('\n', '\r\n')
        _setup_xml = format_str(
                        load_from_path(kwargs['setup_answer']),
                        mac=get_mac(),
                        **dict_include('name','udn','ip', 'tcp_port', 'service', **kwargs)).replace('\n', '\r\n')
        self.setup_answer = format_str(self.xml_header, **{'length': len(_setup_xml)}) + _setup_xml

    @debug.show
    def _ssdpSend(self, **data):
        _params = {'data': date(), 'st': data['st']}
        _message = format_str(self.m_search_response, **_params, **self._ssdp_child)
        Upnp.upnpSend(self, template=_message, address=(data['_REFERER']['ip'],data['_REFERER']['port']))

    @Upnp.upnpEvent
    @debug.show
    def _trigger_ssdp_event(self, alive, byebye, **kwargs):
        if alive:
            Upnp.upnpSend(None,notification_sub_type=Ssdp.SSDP_BYEBYE)
        if byebye:
            Upnp.upnpSend(None,notification_sub_type=Ssdp.SSDP_ALIVE)
        if kwargs is not None:
            if kwargs['_CMD'] == Ssdp.SSDP_SEARCH_HEADER and kwargs['man'] and kwargs['st']:
                _discover = '|'.join(self._ssdp_child['discover_patterns']).replace("*",r"\*")
                _pattern = f"^.*({_discover}).*$"
                if re.match(f"^.*({Ssdp.SSDP_DISCOVER}).*$", kwargs['man']) and re.match(_pattern, kwargs['st']):
                    self._ssdpSend(**kwargs)

    @Tcp.tcpEvent
    @debug.show
    def _trigger_ssdp_tcp_event(self, uri, body=None):
        _payload = {"date": date()}
        _answer = None
        if re.match(self._ssdp_child['setup_path_pattern'],uri):
            _answer = self.setup_answer
        else:
            for _handler in Ssdp._ssdp_tcp_handler:
                _answer = _handler(self, uri, body)
                if _answer:
                    break
        if time.ticks_ms() - self.initialized_ts > Ssdp.SSDP_UPNP_RUNNING_TIME_MS and not self.stopped:
            self.stopped = True
            for _handler in Ssdp._ssdp_tcp_handler:
                _answer = _handler(self, None, {'upnp': False})
        return format_str(_answer, **_payload, **self._ssdp_child)

    @debug.show
    def ssdpEvent(func):
        Ssdp._ssdp_tcp_handler.append(func)
        return func
