from . import peripheral 
from . import uart_service

from .base import state

class BleUartPeripheral(peripheral.BLEPeripheral):

    def __init__(self, ble, name=uart_service.DEFAULT_NAME):
        super().__init__(ble, 
                name=name, 
                service=uart_service.UART_SERVICE, 
                appearance=uart_service.ADV_APPEARANCE_GENERIC_COMPUTER)