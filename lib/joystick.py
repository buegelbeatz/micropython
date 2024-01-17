# https://electropeak.com/learn/full-guide-to-esp32-pinout-reference-what-gpio-pins-should-we-use/

import machine
import uasyncio
from micropython import const


def _wraps(f):
    return lambda f:f

def _log(*data):
    # print('joystick', *data)
    pass

def state():
    _log(f"register state code")
    def decorate_state(func):
        @_wraps(func)
        def wrap_state(self, data):
            # pre-processing should be done here
            _result = func(data)
            # post-processing
            return _result
        Joystick._stateHandler = wrap_state
        return wrap_state
    return decorate_state

class Joystick:

    EVENT_LEFT = const(1)
    EVENT_RIGHT = const(2)
    EVENT_TOP = const(4)
    EVENT_DOWN = const(8)
    EVENT_BUTTON = const(16)

    _stateHandler = None

    def __init__(self, verticalPin=35, horizontalPin=32, buttonPin=16):
        self.verticalPin = machine.ADC(machine.Pin(verticalPin))
        self.verticalPin.atten(machine.ADC.ATTN_11DB)
        self.horizontalPin = machine.ADC(machine.Pin(horizontalPin))
        self.horizontalPin.atten(machine.ADC.ATTN_11DB)
        self.buttonPin = machine.Pin(buttonPin, machine.Pin.IN, machine.Pin.PULL_UP)
        self.lastMessage = 0
        uasyncio.create_task(self.__loop())


    async def __loop(self):
        while True:
            await uasyncio.sleep_ms(10) 
            new_message = 0
            v = self.verticalPin.read()
            if v > 3800:
                new_message |= Joystick.EVENT_DOWN
            if v < 200:
                new_message |= Joystick.EVENT_TOP
            v = self.horizontalPin.read()
            if v < 200:
                new_message |= Joystick.EVENT_LEFT
            if v > 3800:
                new_message |= Joystick.EVENT_RIGHT  
            if not self.buttonPin.value():
                new_message |= Joystick.EVENT_BUTTON 
            if new_message != self.lastMessage:
                # self.callback(new_message)
                self._triggerState(new_message)
                self.lastMessage = new_message
                await uasyncio.sleep_ms(100)

    def _triggerState(self, data):
        if not Joystick._stateHandler:
            _log("no handler for joystick state")
            return
        Joystick._stateHandler(self, data)