import uasyncio
import connector
import ubinascii
import machine

from umqtt.simple import MQTTClient, MQTTException

import tools
import gc

def sub_cb(topic, msg):
  print((topic, msg))
  if topic == b'notification' and msg == b'received':
    print('ESP received hello message')


async def main():
    connection = await connector.Connector()
    tools.elapsed_time('connector done')

    client_id = ubinascii.hexlify(machine.unique_id())

    _mqtt = MQTTClient(client_id, '192.168.2.80')

    _mqtt.set_callback(sub_cb)
    _mqtt.connect()
    _mqtt.subscribe(b'alexa')


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