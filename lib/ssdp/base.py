
import ubinascii
import utime as time
import uhashlib as hashlib

class Base:

    def __init__(self):
        self._received = {}

    def inet_aton(self,addr):
        return bytes(map(int, addr.split('.')))
    
    def request_frequence_check(self, data, time_ms):
        _hash = hashlib.md5(data)
        _key = ubinascii.hexlify(_hash.digest()).decode()
        _time = time.ticks_ms()
        if _key in self._received:
            if _time - self._received[_key] < time_ms:
                self._received[_key] = _time
                return True
            else:
                del(self._received[_key])
        else:
            self._received[_key] = _time
