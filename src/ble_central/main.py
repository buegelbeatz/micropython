import uasyncio
import bluetooth
import ble.uart_central as uart
from display.ttgo import TTGO
from micropython import const
import connector
import http.websocket as websocket
import tools
import gc

# TODO: extract from class module joystick

EVENT_LEFT = const(1)
EVENT_RIGHT = const(2)
EVENT_TOP = const(4)
EVENT_DOWN = const(8)
EVENT_BUTTON = const(16)

async def main():
    tools.elapsed_time('main function started')
    connection = await connector.Connector()
    tools.elapsed_time('connector done')

    @connector.clients()
    def connector_clients(add,remove):
        if add:
            print(f"client '{add}' joined the network")
        if remove:
            print(f"client '{remove}' left the network")

    httpObject = websocket.HTTPWebsocket(
        title=connection.name,
        ip=connection.ip,
        network=connection.network,
        networks=connection.networks)
    tools.elapsed_time('http server done')

    blue = uart.BleUartCentral(bluetooth.BLE(), name='ua01')
    tools.elapsed_time('bluetooth done')

    @websocket.websocketReceive()
    def websocket_notify(request, data):
        print("websocket_notify", request.key, data)
        blue.send(f'r {data}')    

    @websocket.websocketClosed()
    def websocket_closed(request):
        print("websocket_closed", request.key)

    @websocket.websocketOpened()
    def websocket_opened(request):
        print("websocket_opened", request.key)
        request.send('hello')

    display = TTGO()
    tools.elapsed_time('display done')

    # TODO: move over to /lib
    def show_display(data): 
        display.text("#",60,120,TTGO.MAGENTA if int(data) & EVENT_BUTTON else TTGO.GREY)
        display.text("^",60,90,TTGO.YELLOW if int(data) & EVENT_TOP else TTGO.GREY)
        display.text("v",60,150,TTGO.YELLOW if int(data) & EVENT_DOWN else TTGO.GREY)
        display.text("<",30,120,TTGO.YELLOW if int(data) & EVENT_RIGHT else TTGO.GREY)
        display.text(">",90,120,TTGO.YELLOW if int(data) & EVENT_LEFT else TTGO.GREY)

    @uart.state(uart.BleUartCentral.STATE_RECEIVE)
    def notify(data):
        print("notify", data)
        httpObject.webSocketSend(data)
        show_display(data)
        blue.send(data)

    @uart.state(uart.BleUartCentral.STATE_CONNECTED)
    def device_connected(data):
        display.text("connected   ",10,10)
        show_display(0)

    @uart.state(uart.BleUartCentral.STATE_DISCONNECTED)
    def device_disconnected(data):
        display.fill(0)
        display.text("disconnected",10,10)

    @uart.state(uart.BleUartCentral.STATE_CONNECTING)
    def device_connecting(data):
        display.text("scanning... ",10,10)

    print('after initialized', tools.memory_free())
    tools.elapsed_time('main function loop')
    try:
        while True:
            await uasyncio.sleep(10)
            gc.collect()
    except KeyboardInterrupt:
        pass
    blue.close()

uasyncio.run(main()) 