from . import websocket
from .request import Request
import uasyncio

def _log(*data):
    # print('http.connect', *data)
    pass

class HTTPConnect(websocket.HTTPWebsocket):

    PATH = b'/connect'
    TITLE_DEFAULT = 'esp32-unknown'
    IP_DEFAULT = '0.0.0.0'

    def __init__(self, *args, **kwargs):
        _log('HTTPConnect __init__')
        self.title = kwargs['title'] if 'title' in kwargs.keys() else HTTPConnect.TITLE_DEFAULT
        self.ip = kwargs['ip'] if 'ip' in kwargs.keys() else HTTPConnect.IP_DEFAULT
        self.networks = kwargs['networks'] if 'networks' in kwargs.keys() else [] 
        self.network = kwargs['network'] if 'network' in kwargs.keys() else ""
        _networks_options = [ f"<option {'selected' if not self.network else ''}>Access point mode</option>" ]
        for _network in self.networks:
            _networks_options.append(f"<option selected>{_network}</option>" if self.network == _network else f"<option>{_network}</option>")
        del kwargs['networks']
        del kwargs['network']
        super().__init__(*args, networks_options="\r\n".join(_networks_options), **kwargs) # TODO: Is networks here really needed as parameter?
        _networks_options = None

    async def websocket_callback(self, request, data):
        # TODO: Does this really work or should there be just a reload triggered after n seconds from client side
        _log('HTTPConnect websocket_callback')
        print(data)
        try:
            if data['action'] == 'connect':
                # TODO: Filter for action = connect
                # TODO: Try to connect to wifi -> If it works save it and switch back - is it possible in parallel?
                await uasyncio.sleep(5)
                request.send({'action': 'connect', 'data': 'it is done'})
                return 
        except:
            pass
        super().websocket_callback(request, data)

    async def callback(self, request: Request):
        _log('HTTPConnect callback')
        if HTTPConnect.PATH == request.path:
            request.path = b'/templates/connect.html'
            # TODO: Maybe add message here ! request.g['message'] = 'restart'
        for _line in super().callback(request):
            yield _line