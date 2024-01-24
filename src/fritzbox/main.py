import uasyncio
import connector


import tools
import gc


async def main():
    connection = await connector.Connector()
    tools.elapsed_time('connector done')

    # TODO: insert code

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