import uasyncio
import bluetooth
# from ble.uart_peripheral import BleUartPeripheral, state
import ble.uart_peripheral as uart
import joystick

# TODO: WIFI - Form, QR-Code, ...
# TODO: Alternate Websocket 


async def main():

    blue = uart.BleUartPeripheral(bluetooth.BLE(), name='ua01')

    @uart.state(uart.BleUartPeripheral.STATE_RECEIVE)
    def receive(data):
        print('receive', data)

    @joystick.state()
    def notify(data):
        print("notify", data)
        blue.notify(str(data))

    js = joystick.Joystick()

    try:
        while True:
            await uasyncio.sleep(1)
    except KeyboardInterrupt:
        pass
 
    blue.close()

uasyncio.run(main()) 

