import uasyncio
import connector

from ssdp.hue import Hue

import tools
import gc


async def main():
    connection = await connector.Connector()
    tools.elapsed_time('connector done')

    hue = Hue(ip=connection.ip,tcp_port=80)
    hue.devices.add('Buerolampe1')
    hue.devices.add('Buerolampe2')
    hue.devices.add('Buerolampe3')
    
    @hue.hueEvent
    def hue_event(name, type, payload):
        print(name, type, payload)
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