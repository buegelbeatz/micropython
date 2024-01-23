import uasyncio
import connector

from ssdp.belkin import Belkin
# import ssdp.belkin as belkin

import tools
import gc


async def main():
    connection = await connector.Connector()
    tools.elapsed_time('connector done')

    # @connector.clients()
    # def connector_clients(add,remove):
    #     if add:
    #         print(f"client '{add}' joined the network")
    #     if remove:
    #         print(f"client '{remove}' left the network")

    _obj = Belkin(ip=connection.ip,tcp_port=80,name='testlampe')
    print(_obj)



    # @upnp.upnpMessageEvent()
    # def upnp_event(data,alive,byebye):
    #     if alive:
    #         print('upnp - alive')
    #         upnpObject.notify(None,'ssdp:alive')
    #     if byebye:
    #         print('upnp - byebye')
    #         upnpObject.notify(None,'ssdp:byebye')
    #     if data:
    #         print('data', data)

    # alexaObject = alexa.Alexa(
    #     name=connection.name,
    #     ip=connection.ip,
    #     network=connection.network,
    #     networks=connection.networks)
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