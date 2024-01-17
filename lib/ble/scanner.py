from . import base 
from . import bleAdvReader
from micropython import const
import bluetooth
import struct
import uasyncio
import ubinascii

from .base import state

# https://btprodspecificationrefs.blob.core.windows.net/assigned-numbers/Assigned%20Number%20Types/Assigned%20Numbers.pdf


_IRQ_SCAN_RESULT = const(5)
_IRQ_SCAN_DONE = const(6)

def hex(data) :
    if data :
        return ubinascii.hexlify(data).decode().upper()
    return ''

def mac2str(mac) :
    if mac :
        return ubinascii.hexlify(mac, ':').decode().upper()
    return ''

# _adv_types = {}
# _adv_types[base.ADV_TYPE_FLAGS] = 'ADV_TYPE_FLAGS'
# _adv_types[base.ADV_TYPE_NAME] = 'ADV_TYPE_NAME'
# _adv_types[base.ADV_TYPE_SHORT_NAME] = 'ADV_TYPE_SHORT_NAME'
# _adv_types[base.ADV_TYPE_DEVICE_ID] = 'ADV_TYPE_DEVICE_ID'
# _adv_types[base.ADV_TYPE_UUID16_COMPLETE] = 'ADV_TYPE_UUID16_COMPLETE'
# _adv_types[base.ADV_TYPE_UUID32_COMPLETE] = 'ADV_TYPE_UUID32_COMPLETE'
# _adv_types[base.ADV_TYPE_UUID128_COMPLETE] = 'ADV_TYPE_UUID128_COMPLETE'
# _adv_types[base.ADV_TYPE_UUID16_MORE] = 'ADV_TYPE_UUID16_MORE'
# _adv_types[base.ADV_TYPE_UUID32_MORE] = 'ADV_TYPE_UUID32_MORE'
# _adv_types[base.ADV_TYPE_UUID128_MORE] = 'ADV_TYPE_UUID128_MORE'
# _adv_types[base.ADV_TYPE_APPEARANCE] = 'ADV_TYPE_APPEARANCE'
# _adv_types[base.ADV_TYPE_CUSTOMDATA] = 'ADV_TYPE_CUSTOMDATA'
# _adv_types[base.ADV_TYPE_PUBLIC_TARGET_ADDRESS] = 'ADV_TYPE_PUBLIC_TARGET_ADDRESS'
# _adv_types[base.ADV_TYPE_SERVICE_DATA_16] = 'ADV_TYPE_SERVICE_DATA_16'
# _adv_types[base.ADV_TYPE_SERVICE_DATA_128] = 'ADV_TYPE_SERVICE_DATA_128'
# _adv_types[base.ADV_TYPE_TX_POWER_LEVEL] = 'ADV_TYPE_TX_POWER_LEVEL'
# _adv_types[base.ADV_TYPE_SUPPORTED_FEATURES] = 'ADV_TYPE_SUPPORTED_FEATURES'

def _log(*data):
    # print('ble.scanner', *data)
    pass

class BLEScanner(base.BLEBase):

    def __init__(self, ble):
        super().__init__(ble, name='scanner')
        self._ble.config(rxbuf=2048)
        self._triggerState(BLEScanner.STATE_INITIALIZE,None)
        uasyncio.create_task(self._loop()) 
        self._devices = {}

    # def _decode_fields(self, payload):
    #     # https://docs.silabs.com/bluetooth/2.13/code-examples/stack-features/adv-and-scanning/adv-manufacturer-specific-data
    #     offset = 0
    #     result = []
    #     while offset + 1 < len(payload):
    #         length,type = payload[offset], payload[offset+1]
    #         result.append({'adv_type': type, 'payload': payload[offset + 2 : offset + length + 1]})
    #         offset += 1 + payload[offset]
    #     return result

    @base.irq(_IRQ_SCAN_RESULT) # 5
    def _scan_result(self, data):
        _addr_type, addr, _connectable, rssi, adv_data = data
        _addr_raw = bytes(addr)
        # _addr = ubinascii.hexlify(_addr_raw).decode()
        _data = bytes(adv_data)
        mac = mac2str(addr)
        print()
        print()
        print('  - MAC ADDRESS  : %s' % mac)
        print('  - RSSI         : %s' % rssi)
        try :
            r = bleAdvReader.BLEAdvReader(_data)
            for advObj in r.GetAllElements() :
                print('  - OBJECT       : [%s] %s' % (type(advObj), advObj))
        except :
            pass


#         if not _addr in self._devices.keys():
#             self._devices[_addr] = {'addr' : _addr_raw, 'addr_type': _addr_type, 'connectable':_connectable, 'rssi': rssi, 'hex': ubinascii.hexlify(_data).decode()}
#         _results = self._decode_fields(_data)
#         for _result in _results:
#             if _result['adv_type'] in _adv_types.keys():
#                 if _result['adv_type'] != base.ADV_TYPE_CUSTOMDATA:
#                     self._devices[_addr][_adv_types[_result['adv_type']]] = _result['payload']
#                 else:
#                     self._devices[_addr][_adv_types[_result['adv_type']]] = {
#                         #'payload': _result['payload'],
#                         # 'converted':[(i,_result['payload'][i]) for i in range(len(_result['payload']))], 
#                         'hex': ubinascii.hexlify(_result['payload']).decode(),
#                         'custom':{}}
                    
# # custom payloads:
# #{'44d09882bdab': {'ADV_TYPE_CUSTOMDATA': 
# #   {'flag': b'L\x00\x0c', 'custom': {'ADV_TYPE_SHORT_NAME': b'\x85\x88\xd2M\xdb\x1a\x8f\x0e\xad\x10\xed\x81*', 'ADV_TYPE_UUID32_COMPLETE': b'N\x1c\x98\xab\xb3'}, 
# #       'converted': [(0, 76), (1, 0), (2, 12), (3, 14), (4, 8), (5, 133), (6, 136), (7, 210), (8, 77), (9, 219), (10, 26), (11, 143), (12, 14), (13, 173), (14, 16), (15, 237), (16, 129), (17, 42), (18, 16), (19, 5), (20, 78), (21, 28), (22, 152), (23, 171), (24, 179)]}, 'ADV_TYPE_FLAGS': b'\x1a', 'addr': '44d09882bdab', 'rssi': -49}, 
# # '0931b458e77e': {'ADV_TYPE_CUSTOMDATA': 
# #   {'flag': b'\x06\x00\x01', 'custom': {'unknown_44': b'\xe3\x94[a\x19L9f-*L\x98\x1cb', 'unknown_32': b'\x02\x81\xe68Pa\xf8J'}, 
# #       'converted': [(0, 6), (1, 0), (2, 1), (3, 9), (4, 32), (5, 2), (6, 129), (7, 230), (8, 56), (9, 80), (10, 97), (11, 248), (12, 74), (13, 176), (14, 44), (15, 227), (16, 148), (17, 91), (18, 97), (19, 25), (20, 76), (21, 57), (22, 102), (23, 45), (24, 42), (25, 76), (26, 152), (27, 28), (28, 98)]}, 'addr': '0931b458e77e', 'rssi': -78}, 
# # '2d27f6c2c5b9': {'ADV_TYPE_CUSTOMDATA': 
# #   {'flag': b'L\x00\t', 'custom': {'ADV_TYPE_UUID16_COMPLETE': b'\x12\xc0\xa8\x02\xf7'}, 
# #       'converted': [(0, 76), (1, 0), (2, 9), (3, 6), (4, 3), (5, 18), (6, 192), (7, 168), (8, 2), (9, 247)]}, 'ADV_TYPE_FLAGS': b'\x1a', 'addr': '2d27f6c2c5b9', 'rssi': -49}, 
# # 'fcdde91e84f7': {'ADV_TYPE_CUSTOMDATA': 
# #   {'flag': b'L\x00\x12', 'custom': {}, 
# #       'converted': [(0, 76), (1, 0), (2, 18), (3, 2), (4, 0), (5, 3)]}, 'addr': 'fcdde91e84f7', 'rssi': -50}, 
# # 'c2be8df8a48f': {'ADV_TYPE_CUSTOMDATA': 
# #   {'flag': b'L\x00\x12', 'custom': {}, 'converted': [(0, 76), (1, 0), (2, 18), (3, 2), (4, 0), (5, 2)]}, 'addr': 'c2be8df8a48f', 'rssi': -35}, 
# # '7517704fb2bc': {'ADV_TYPE_CUSTOMDATA': 
# #   {'flag': b'L\x00\x10', 'custom': {'unknown_42': b'\x1e.\x91A\xe7'}, 
# #       'converted': [(0, 76), (1, 0), (2, 16), (3, 6), (4, 42), (5, 30), (6, 46), (7, 145), (8, 65), (9, 231)]}, 'rssi': -38, 'ADV_TYPE_TX_POWER_LEVEL': b'\x07', 'addr': '7517704fb2bc', 'ADV_TYPE_FLAGS': b'\x1a'}, 
# # '161075a6fb6b': {
# #   'ADV_TYPE_UUID16_COMPLETE': b'o\xfd', 
# #   'ADV_TYPE_SERVICE_DATA_16': b'o\xfd\x1f:\xe6\xf8\x89\x03\xe6\x05R\x06q\x0f-\xbd6\x89\xb3\xb5\xb4\x1a', 
# #   'addr': '161075a6fb6b', 
# #   'rssi': -37}, 
# # '612fca2ddd15': {'ADV_TYPE_CUSTOMDATA': 
# #   {'flag': b'L\x00\x0c', 'custom': {'ADV_TYPE_SHORT_NAME': b'\x86\x88\x96\xa6\xa9\xb5\x9d\x83\x93ST\xeb\x0c', 'ADV_TYPE_UUID32_COMPLETE': b'N\x1c\x98\xab\xb3'}, 
# #       'converted': [(0, 76), (1, 0), (2, 12), (3, 14), (4, 8), (5, 134), (6, 136), (7, 150), (8, 166), (9, 169), (10, 181), (11, 157), (12, 131), (13, 147), (14, 83), (15, 84), (16, 235), (17, 12), (18, 16), (19, 5), (20, 78), (21, 28), (22, 152), (23, 171), (24, 179)]}, 'ADV_TYPE_FLAGS': b'\x1a', 'addr': '612fca2ddd15', 'rssi': -47}}


#                     _custom_results = self._decode_fields(_result['payload'][3:])
#                     self._devices[_addr][_adv_types[_result['adv_type']]]['manufacturer'] = ubinascii.hexlify(_result['payload'][1].to_bytes(1, 'big') + _result['payload'][0].to_bytes(1, 'big')).decode()
#                     for _custom_result in _custom_results:
#                         if _custom_result['adv_type'] in _adv_types.keys():
#                             self._devices[_addr][_adv_types[_result['adv_type']]]['custom'][_adv_types[_custom_result['adv_type']]] = _custom_result['payload'] # \
#                                 #if _custom_result['adv_type'] != base.ADV_TYPE_NAME and _custom_result['adv_type'] != base.ADV_TYPE_SHORT_NAME else _custom_result['payload'].decode()
#                             # if _adv_types[_custom_result['adv_type']] == 'ADV_TYPE_SHORT_NAME':
#                             #     _short_name = struct.unpack("<{}s".format(len(_custom_result['payload'])), _custom_result['payload'])[0]
#                             #     self._devices[_addr][_adv_types[_result['adv_type']]]['custom']['short_name'] = _short_name # .decode('utf-8')
#                         else:
#                             if _custom_result['adv_type']:
#                                 self._devices[_addr][_adv_types[_result['adv_type']]]['custom']['unknown_'+ str(_custom_result['adv_type'])] = _custom_result['payload']
#             else:
#                 if _result['adv_type']:
#                     self._devices[_addr]['unknown_'+ str(_result['adv_type'])] = _result['payload']


    @base.irq(_IRQ_SCAN_DONE) # 6
    def _scan_done(self, data):
        _log('scanning done')
        # TODO: stop scanning and try to connect to devices
        # Wait until all connections are tested
        self._triggerState(BLEScanner.STATE_FOUND,self._devices)
        self._devices = {}

    async def _loop(self):
        _timeout = 3000
        while True: # TODO: Error handling!
            try:
                self._triggerState(BLEScanner.STATE_CONNECTING,None)
                self._ble.gap_scan(_timeout, 30000, 30000)
            except:
                pass
            await uasyncio.sleep_ms(_timeout)
            await uasyncio.sleep_ms(1000)
