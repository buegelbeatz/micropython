from . import base 
import struct
from micropython import const


_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)

class BLEPeripheral(base.BLEBase):

    def __init__(self, ble, name=None, service=None, appearance=0, rxbuf=100):
        super().__init__(ble, name=name)
        self._triggerState(BLEPeripheral.STATE_INITIALIZE,None)
        self._ble.config(gap_name=self._name)
        self._services = [service]
        self._appearance = appearance
        ((self._tx_handle, self._rx_handle),) = self._ble.gatts_register_services(self._services)
        self._ble.gatts_set_buffer(self._rx_handle, rxbuf, True)
        self._connections = set()
        self._rx_buffer = bytearray()
        self._payload = self._advertising_payload()
        self._triggerState(BLEPeripheral.STATE_CONNECTING,None)
        self._ble.gap_advertise(100000, adv_data=self._payload)

    def _advertising_payload(self, limited_disc=False, br_edr=False):
        payload = bytearray()
        def _append(adv_type, value):
            nonlocal payload
            payload += struct.pack("BB", len(value) + 1, adv_type) + value

        _append(base.ADV_TYPE_FLAGS,
            struct.pack("B", (0x01 if limited_disc else 0x02) + (0x18 if br_edr else 0x04)))
        if self._name:
            _append(base.ADV_TYPE_NAME, self._name)
        if self._services:
            for service in self._services:
                b = bytes(service[0])
                if len(b) == 2:
                    _append(base.ADV_TYPE_UUID16_COMPLETE, b)
                elif len(b) == 4:
                    _append(base.ADV_TYPE_UUID32_COMPLETE, b)
                elif len(b) == 16:
                    _append(base.ADV_TYPE_UUID128_COMPLETE, b)
        if self._appearance:
            _append(base.ADV_TYPE_APPEARANCE, struct.pack("<h", self._appearance))
        return payload

    def notify(self, data):
        self._triggerState(BLEPeripheral.STATE_SEND,None)
        for conn_handle in self._connections:
            self._ble.gatts_notify(conn_handle, self._tx_handle, data)

    def close(self):
        for conn_handle in self._connections:
            self._ble.gap_disconnect(conn_handle)
        self._connections.clear()
        self._triggerState(BLEPeripheral.STATE_DISCONNECTED,None)

    @base.irq(_IRQ_CENTRAL_CONNECT)
    def _connect(self, data):
        conn_handle, _, _ = data
        self._connections.add(conn_handle)
        self._triggerState(BLEPeripheral.STATE_CONNECTED,len(self._connections))

    @base.irq(_IRQ_CENTRAL_DISCONNECT)
    def _disconnect(self, data):
        conn_handle, _, _ = data
        if conn_handle in self._connections:
            self._connections.remove(conn_handle)
        if len(self._connections):
            self._triggerState(BLEPeripheral.STATE_CONNECTED,len(self._connections))
        else:
            self._triggerState(BLEPeripheral.STATE_CONNECTING,None)
        self._ble.gap_advertise(500000, adv_data=self._payload)

    @base.irq(_IRQ_GATTS_WRITE)
    def _receive(self, data):
        _, value_handle = data
        value = self._ble.gatts_read(value_handle)
        if value_handle == self._rx_handle:
            self._triggerState(BLEPeripheral.STATE_RECEIVE,value)
