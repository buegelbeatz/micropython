from . import base 
from micropython import const
import bluetooth
import struct
import uasyncio

_IRQ_SCAN_RESULT = const(5)
_IRQ_SCAN_DONE = const(6)
_IRQ_PERIPHERAL_CONNECT = const(7)
_IRQ_PERIPHERAL_DISCONNECT = const(8)
_IRQ_GATTC_SERVICE_RESULT = const(9)
_IRQ_GATTC_CHARACTERISTIC_RESULT = const(11)
_IRQ_GATTC_CHARACTERISTIC_DONE = const(12)
_IRQ_GATTC_WRITE_DONE = const(17)
_IRQ_GATTC_NOTIFY = const(18)

def _log(*data):
    # print('ble.central', *data)
    pass

class BLECentral(base.BLEBase):

    def __init__(self, ble, name=None, service=None):
        super().__init__(ble, name=name)
        self._triggerState(BLECentral.STATE_INITIALIZE,None)
        self._service = service
        self._reset()
        uasyncio.create_task(self._loop()) 

    def _reset(self):
        self._addr_type = None
        self._addr = None
        self._not_found = None
        self._conn_handle = None
        self._tx_handle = None
        self._rx_handle = None

    def _decode_field(self, payload, adv_type):
        i = 0
        result = []
        while i + 1 < len(payload):
            if payload[i + 1] == adv_type:
                result.append(payload[i + 2 : i + payload[i] + 1])
            i += 1 + payload[i]
        return result

    def _decode_name(self, payload):
        n = self._decode_field(payload, base.ADV_TYPE_NAME)
        return str(n[0], "utf-8") if n else ""

    def _decode_services(self, payload):
        services = []
        try:
            for u in self._decode_field(payload, base.ADV_TYPE_UUID16_COMPLETE):
                services.append(bluetooth.UUID(struct.unpack("<h", u)[0]))
            for u in self._decode_field(payload, base.ADV_TYPE_UUID32_COMPLETE):
                services.append(bluetooth.UUID(struct.unpack("<d", u)[0]))
            for u in self._decode_field(payload, base.ADV_TYPE_UUID128_COMPLETE):
                services.append(bluetooth.UUID(u))
        except Exception as e:
            _log('_decode_services', e)
        return services

    @base.irq(_IRQ_SCAN_RESULT) # 5
    def _scan_result(self, data):
        addr_type, addr, _, _, adv_data = data
        # services = self._decode_services(adv_data)
        if self._service[0] in self._decode_services(adv_data) and \
           self._name is self._decode_name(adv_data):
            self._addr_type = addr_type
            self._addr = bytes(addr) # Note: The addr buffer is owned by modbluetooth, need to copy it.
            self._ble.gap_scan(None)

    @base.irq(_IRQ_SCAN_DONE) # 6
    def _scan_done(self, data):
        if self._addr_type is not None and self._addr is not None:
            try:
                self._ble.gap_connect(self._addr_type, self._addr)
            except:
                pass
        else:
            self._not_found = True

    @base.irq(_IRQ_PERIPHERAL_CONNECT) # 7
    def _peripheral_connected(self, data):
        conn_handle, addr_type, addr, = data
        if addr_type == self._addr_type and addr == self._addr:
            self._conn_handle = conn_handle
            self._ble.gattc_discover_services(self._conn_handle)
        else:
            self._not_found = True

    @base.irq(_IRQ_PERIPHERAL_DISCONNECT) # 8
    def _peripheral_disconnected(self, data):
        conn_handle, _, _, = data
        if conn_handle == self._conn_handle:
            self._reset()
            self._triggerState(BLECentral.STATE_DISCONNECTED,None)

    @base.irq(_IRQ_GATTC_SERVICE_RESULT) # 9
    def _service_result(self, data):
        conn_handle, start_handle, end_handle, uuid = data
        if conn_handle == self._conn_handle and uuid == self._service[0]:
            self._ble.gattc_discover_characteristics(self._conn_handle, start_handle, end_handle)
        else:
            self._not_found = True

    @base.irq(_IRQ_GATTC_CHARACTERISTIC_RESULT) # 11
    def _chracteristic_result(self, data):
        conn_handle, _, value_handle, _, uuid = data
        if conn_handle == self._conn_handle:
            if uuid == self._service[1][1][0]:
                self._rx_handle = value_handle
            if uuid == self._service[1][0][0]:
                self._tx_handle = value_handle

    @base.irq(_IRQ_GATTC_CHARACTERISTIC_DONE) # 12
    def _chracteristic_done(self, data):
            if self._tx_handle is None or self._rx_handle is None:
                print("Failed to find uart rx characteristic.")
                self._not_found = True
            else:
                self._not_found = False
                self._triggerState(BLECentral.STATE_CONNECTED,None)

    @base.irq(_IRQ_GATTC_WRITE_DONE)
    def _send_done(self, data):
        self._triggerState(BLECentral.STATE_SENT,data)
    
    @base.irq(_IRQ_GATTC_NOTIFY) # 18
    def _notify(self, data):
        conn_handle, value_handle, notify_data = data
        if conn_handle == self._conn_handle and value_handle == self._tx_handle:
            data_str = str(notify_data, 'utf-8')
            self._triggerState(BLECentral.STATE_RECEIVE,data_str)
    
    def is_connected(self):
        return self._conn_handle is not None and self._tx_handle is not None and \
                self._tx_handle is not None and self._not_found is False

    async def _loop(self):
        _timeout = 1000
        self._not_found = None
        while True: # TODO: Error handling!
            if not self.is_connected():
                try:
                    self._triggerState(BLECentral.STATE_CONNECTING,None)
                    self._ble.gap_scan(_timeout, 30000, 30000)
                except:
                    pass
                await uasyncio.sleep_ms(_timeout)
            await uasyncio.sleep_ms(1000)

    def disconnect(self):
        if self._conn_handle:
            self._ble.gap_disconnect(self._conn_handle)
            self._reset()
            self._triggerState(BLECentral.STATE_DISCONNECTED,None)

    def send(self, data, response=False):
        if self.is_connected():
            self._triggerState(BLECentral.STATE_SEND,data)
            self._ble.gattc_write(self._conn_handle, self._rx_handle, data, 1 if response else 0)