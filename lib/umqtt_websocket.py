from umqtt.simple import MQTTClient, MQTTException
try:
    import usocket as socket
except:
    import socket
from websocket import websocket
import ussl

class WebsocketNew(websocket):
    def setblocking(self, switch):
        try:
            if switch:
                self.ioctl(0xFF, 0x80)
            else:
                self.ioctl(0xFF, 0x00)
        except:
            pass

class MQTTWebsocketClient(MQTTClient):

    def __create_websocket(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect(socket.getaddrinfo(self.server, self.port)[0][-1])
            if self.ssl:
                self.sock = ussl.wrap_socket(self.sock, **self.ssl_params)
            websocket_upgrade_headers = (
                "GET /mqtt HTTP/1.1", "Host: {host}",
                "Connection: Upgrade", "Upgrade: websocket",
                "Sec-WebSocket-Key: aSk+xCH/A9ZbxvqjxF8itg==",
                "Sec-WebSocket-Protocol: mqttv3.1",
                "Sec-WebSocket-Version: 13","", ""
            )
            self.sock.write("\r\n".join(websocket_upgrade_headers).format(host=self.server).encode())
            upgrade_done = False
            response_line = self.sock.readline()
            while response_line:
                if "sec-websocket-accept" in response_line.lower():
                    upgrade_done = True
                if response_line == b'\r\n':
                    break
                response_line = self.sock.readline()
            if upgrade_done:
                self.sock = WebsocketNew(self.sock)
                return
        except:
            pass
        raise MQTTException("could not create websocket.")

    def __connect(self, clean_session):
        premsg = bytearray(b"\x10\0\0\0\0\0")
        msg = bytearray(b"\x04MQTT\x04\x02\0\0")

        sz = 10 + 2 + len(self.client_id)
        msg[6] = clean_session << 1
        if self.user is not None:
            sz += 2 + len(self.user) + 2 + len(self.pswd)
            msg[6] |= 0xC0
        if self.keepalive:
            assert self.keepalive < 65536
            msg[7] |= self.keepalive >> 8
            msg[8] |= self.keepalive & 0x00FF
        if self.lw_topic:
            sz += 2 + len(self.lw_topic) + 2 + len(self.lw_msg)
            msg[6] |= 0x4 | (self.lw_qos & 0x1) << 3 | (self.lw_qos & 0x2) << 3
            msg[6] |= self.lw_retain << 5

        i = 1
        while sz > 0x7F:
            premsg[i] = (sz & 0x7F) | 0x80
            sz >>= 7
            i += 1
        premsg[i] = sz

        self.sock.write(premsg, i + 2)
        self.sock.write(msg)
        self._send_str(self.client_id)
        if self.lw_topic:
            self._send_str(self.lw_topic)
            self._send_str(self.lw_msg)
        if self.user is not None:
            self._send_str(self.user)
            self._send_str(self.pswd)
        resp = self.sock.read(4)
        assert resp[0] == 0x20 and resp[1] == 0x02
        if resp[3] != 0:
            raise MQTTException(resp[3])
        return resp[2] & 1

    def connect(self, clean_session=True):
        self.__create_websocket()
        self.__connect(clean_session)
     