from . import central 
from . import uart_service

from .base import state

class BleUartCentral(central.BLECentral):

    def __init__(self, ble, name=uart_service.DEFAULT_NAME):
        super().__init__(ble, 
                name=name, 
                service=uart_service.UART_SERVICE)