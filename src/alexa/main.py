import uasyncio
import connector
import neopixel
import machine

from alexa.hue import Hue

import tools
import gc

# TODO: events not as static collections
# TODO: eventbus concept
# TODO: State as payload in event
# TODO: Persistance of bulb states
# TODO: Convert Umlaute and to lower for namings
# TODO: More specific devices: switch, dimmer, bulb, .... 
# TODO: debouncer for udp and ssdp
# TODO: More specific hue events
# TODO: Backup Belkin
# TODO: fix color issue
# TODO: Dynamic devices via mqtt


async def main():
    np = neopixel.NeoPixel(machine.Pin(14), 5)
    np[0] = (0, 0, 16)
    np.write()
    connection = await connector.Connector()
    np[0] = (0,16,0)
    np.write()
    tools.elapsed_time('connector done')

    hue = Hue(ip=connection.ip,tcp_port=80)
    hue.devices.add('Buerolampe1')
    hue.devices.add('Buerolampe2')
    hue.devices.add('Buerolampe3')
    
    @hue.hueEvent
    def hue_event(name, type, payload):
        print(name, type, payload)
        # TODO: setUpnp False
        if type != 'setState':
            return
        ct_min = 383
        ct_max = 199
        _map = {'Buerolampe1': 2,'Buerolampe2': 3,'Buerolampe3': 4}
        ct_min_tuple = (255,243,184)
        ct_max_tuple = (255,255,255)
        if 'bri' in payload:
            _bri_f = 1 - (254 - payload['bri']) / 254
        else:
            _bri_f = 254

        if 'on' in payload and payload['on']:
            if 'colormode' not in payload:
                    np[_map[name]] = (int(128 * _bri_f),int(128 * _bri_f),int(128 * _bri_f))
                    np.write()

            if 'colormode' in payload:
                if payload['colormode'] == 'ct':
                    _wr = 255 + payload['ct'] * (255-255)/(ct_max - ct_min)
                    _wg = 243 + payload['ct'] * (255-243)/(ct_max - ct_min)
                    _wb = 184 + payload['ct'] * (255-184)/(ct_max - ct_min)
                    np[_map[name]] = (int(_wr/2),int(_wg/2),int(_wb/2))
                    np.write()

                if payload['colormode'] == 'hs':
                    np[_map[name]] = (int(_bri_f * payload['red']/2),int(_bri_f * payload['green']/2),int(_bri_f * payload['blue']/2))
                    np.write()
        else:
            np[_map[name]] = (0,0,0)
            np.write()

        # np[0] = (0,0,64)
        # np.write()
        # TODO: Setup mqtt connector

    tools.elapsed_time('server done')

    print('after initialized', tools.memory_free())
    tools.elapsed_time('main function loop')
    try:
        while True:
            await uasyncio.sleep(10)
            gc.collect()
    except KeyboardInterrupt:
        pass

tools.elapsed_time('main function started')
uasyncio.run(main()) 