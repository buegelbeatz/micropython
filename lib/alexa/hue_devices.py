# https://github.com/Aircoookie/Espalexa/blob/main/src/Espalexa.h
# https://dresden-elektronik.github.io/deconz-rest-doc/endpoints/lights/

import json
import ubinascii
import math
import uhashlib as hashlib

from ssdp.tools import load_from_path, get_mac, format_str, dict_exclude

# https://gist.github.com/mathebox/e0805f72e7db3269ec22

def hsv_to_rgb(h, s, v):
    i = math.floor(h*6)
    f = h*6 - i
    p = v * (1-s)
    q = v * (1-f*s)
    t = v * (1-(1-f)*s)

    r, g, b = [
        (v, t, p),
        (q, v, p),
        (p, v, t),
        (p, q, v),
        (t, p, v),
        (v, p, q),
    ][int(i%6)]

    return r, g, b

def hue_sat_to_rgb(hue, sat):
    hue = hue / 65535.0
    sat = sat / 254.0
    r, g, b = hsv_to_rgb(hue,sat, 1)
    return int(r * 255), int(g * 255), int(b * 255)


def rgb_to_hue_sat(rgb):
    r, g, b = rgb
    r, g, b = r / 255.0, g / 255.0, b / 255.0

    cmax = max(r, g, b)
    cmin = min(r, g, b)
    delta = cmax - cmin

    # Calculate hue
    if delta == 0:
        hue = 0
    elif cmax == r:
        hue = 60 * (((g - b) / delta) % 6)
    elif cmax == g:
        hue = 60 * (((b - r) / delta) + 2)
    elif cmax == b:
        hue = 60 * (((r - g) / delta) + 4)

    # Calculate saturation
    if cmax == 0:
        sat = 0
    else:
        sat = delta / cmax

    # Scale values to the expected ranges
    hue = int(hue * 65535 / 360)
    sat = int(sat * 254)

    return hue, sat




class HueDevices():
    def __init__(self):
        self._devices = {}
        self._index = 1

    def add(self,name):
        self._devices[str(self._index)] = HueDevice(name)
        self._index += 1

    def get_all(self):
        _payload = {}
        for _key, _value in self._devices.items():
            _payload[_key] = _value.json()
        return _payload
    
    def get(self,key):
        if key in self._devices:
            return self._devices[key]
        return None



class HueDeviceType():
    COLOR = 1
    DIM = 2
    SWITCH = 3

class HueDevice():

    TEMLATES_ROOT = "/ssdp/hue_"
    JSON_DEVICE = f"{TEMLATES_ROOT}device.json"

    def __init__(self, name=None):
        self.name = name
        self.on = False
        self.colormode = "hs"
        self.bri = 0
        self.hue = 0
        self.sat = 0
        self.ct = 500 # TODO:         "ct": {ct}, + colormode: "ct"
        # effects = 
        self.x = 0.0
        self.y = 0.0
        _hash = hashlib.md5(name + get_mac())
        _md5 = ubinascii.hexlify(_hash.digest()).decode()
        self.id = f"{_md5[0:2]}:{_md5[2:4]}:{_md5[4:6]}:{_md5[6:8]}:{_md5[8:10]}:{_md5[10:12]}:00:11-{_md5[12:14]}"
        self.long_info_template = load_from_path(HueDevice.JSON_DEVICE).replace('\n', '\r\n')

    def json(self):
        _on = 'true' if self.on else 'false'
        return json.loads(format_str(self.long_info_template,on=_on,**dict_exclude('on', **self.__dict__)))