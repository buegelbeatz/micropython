# This file is executed on every boot (including wake-boot from deepsleep)
import esp
import esp32
import micropython
import gc
import tools

# uos.dupterm(None, 1) # disable REPL on UART(0)
esp.osdebug(None) # 0
gc.collect()
gc.enable()

micropython.alloc_emergency_exception_buf(200)

tools.elapsed_time('boot started')

print('before initialized', tools.memory_free())
print('before initialized', tools.disk_free())
try:
    print('hall sensor', esp32.hall_sensor())
except:
    pass
print('temperature', f"{(esp32.raw_temperature() - 32) * 5/9:0.0f}" )
tools.elapsed_time('boot done')