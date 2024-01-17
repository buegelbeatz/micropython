import bluetooth
from micropython import const

# Advertising payloads are repeated packets of the following form:
#   1 byte data length (N + 1)
#   1 byte type (see constants below)
#   N bytes type-specific data

ADV_TYPE_FLAGS = const(0x1)
ADV_TYPE_NAME = const(0x9)
ADV_TYPE_SHORT_NAME = const(0x8)
ADV_TYPE_DEVICE_ID = const(0x10)
ADV_TYPE_UUID16_COMPLETE = const(0x3)
ADV_TYPE_UUID32_COMPLETE = const(0x5)
ADV_TYPE_UUID128_COMPLETE = const(0x7)
ADV_TYPE_UUID16_MORE = const(0x2)
ADV_TYPE_UUID32_MORE = const(0x4)
ADV_TYPE_UUID128_MORE = const(0x6)
ADV_TYPE_APPEARANCE = const(0x19)
ADV_TYPE_CUSTOMDATA = const(0xff) 
ADV_TYPE_PUBLIC_TARGET_ADDRESS = const(0x17)
ADV_TYPE_SERVICE_DATA_16 = const(0x16)
ADV_TYPE_TX_POWER_LEVEL = const(0xa)
ADV_TYPE_SUPPORTED_FEATURES = const(0x27)
ADV_TYPE_SERVICE_DATA_128 = const(0x21)

def _wraps(f):
    return lambda f:f

def _log(*data):
    # print('ble.base', *data)
    pass

def irq(event=0):
    _log(f"register event code {event}")
    def decorate_irq(func):
        @_wraps(func)
        def wrap_irq(self, data):
            # pre-processing should be done here
            return func(self, data)
        BLEBase._eventHandler[str(event)] = wrap_irq
        return wrap_irq
    return decorate_irq

def state(currentState=0):
    _log(f"register state code {currentState}")
    def decorate_state(func):
        @_wraps(func)
        def wrap_state(self,data):
            # pre-processing should be done here
            return func(data)
        BLEBase._stateHandler[str(currentState)] = wrap_state
        return wrap_state
    return decorate_state

class BLEBase:

    STATE_UNKNOWN = const(0)
    STATE_INITIALIZE = const(1)
    STATE_CONNECTING = const(2)
    STATE_CONNECTED = const(3)
    STATE_DISCONNECTED = const(4)
    STATE_SEND = const(5)
    STATE_SENT = const(6)
    STATE_RECEIVE = const(7)
    STATE_FOUND = const(8)

    _stateHandler = {}
    _eventHandler = {}

    def __init__(self, ble, name='mipy'):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        self._name = name[:4] # somehow longer names don't work at the moment

    def _irq(self, event, data):
        _log(event, data)
        if str(event) not in BLEBase._eventHandler.keys():
            _log(f"no handler for event {event}")
            return
        BLEBase._eventHandler[str(event)](self, data)

    def _triggerState(self, currentState, data):
        _log(currentState, data)
        if str(currentState) not in BLEBase._stateHandler.keys():
            _log(f"no handler for state {currentState}")
            return
        BLEBase._stateHandler[str(currentState)](self, data)
