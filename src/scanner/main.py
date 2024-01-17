import uasyncio
import bluetooth
import ble.scanner as scanner

import connector
import http.websocket as websocket
import tools
import gc
import time


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

    _devices = {}

    blue = scanner.BLEScanner(bluetooth.BLE())
    tools.elapsed_time('bluetooth done')

    def _distance(rssi):
        return 10 ** ((-69 - rssi)/(10 * 2))

    @scanner.state(scanner.BLEScanner.STATE_FOUND)
    def device_connected(data):
        print(data)
        # for _, _device in data.items():
        #     if 'ADV_TYPE_CUSTOMDATA' in _device.keys():
        #         _key = str(hash(_device['ADV_TYPE_CUSTOMDATA']))
        #         _value = _distance(_device['rssi'])
        #         if not _key in _devices.keys():
        #             if _value < 10:
        #                 _devices[_key] = _device
        #                 _devices[_key]['distance'] = _value
        #         else:
        #             if _value > 12:
        #                 del _devices[_key]
        #             else:
        #                 if abs(_value - _devices[_key]['distance']) > max(2,_value * _value / 4):
        #                     _new_value = (_value + _devices[_key]['distance'])/2
        #                     print(_key, _devices[_key], 'moving')
        #                     _devices[_key]['distance'] = _new_value


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