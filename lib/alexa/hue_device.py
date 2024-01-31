import ubinascii
import machine
import hashlib
import json
import os

class HueGenericDevice():

    MANUFACTURER = "Philips"
    SW_VERSION = "66012040"

    def __init__(self, name):
        self.name = self._clean_name(name)
        _hash = hashlib.md5(self.name + ubinascii.hexlify(machine.unique_id()).decode())
        _md5 = ubinascii.hexlify(_hash.digest()).decode()
        self.uniqueid = f"{_md5[0:2]}:{_md5[2:4]}:{_md5[4:6]}:{_md5[6:8]}:{_md5[8:10]}:{_md5[10:12]}:00:11-{_md5[12:14]}"
        self.manufacturername = HueGenericDevice.MANUFACTURER
        self.swversion = HueGenericDevice.SW_VERSION
        self.hascolor = False
        self.state = {  "on" : False,
                        "reachable": True,
                        'effect': "none",
                        "alert": "none"
                        }
    def _clean_name(self,name):
        umlaut_mapping = { 'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss'}
        _name = name.lower()
        for umlaut, base_char in umlaut_mapping.items():
            _name = _name.replace(umlaut, base_char)
        return "".join(_name.split())

    def _file_name(self):
        return f".hue.light.{self.name}.state.json"

    def load_state(self):
        try:
            with open(self._file_name, 'r') as file:
                self.state = json.loads(file.read())
        except OSError:
            print("Error: Unable to open file for reading")

    def save_state(self):
        try:
            with open(self._file_name, 'w') as file:
                file.write(json.dumps(self.state))
        except OSError:
            print("Error: Unable to open file for writing")

    def get_device(self):
        return json.dumps(self)

    def set_state(self, id, payload):
        _answer = []
        for _key, _value in payload.items():
            if _key in self.state:
                self.state[_key] = _value
                _answer.append({'success':{f"/lights/{id}/state/{_key}":_value}})
        return json.dumps(_answer)

class HueDimDevice(HueGenericDevice):

    def __init__(self,name):
        HueGenericDevice.__init__(self,name)
        self.state['bri'] = 0
    
    def set_state(self,id, payload):
        if 'on' in payload:
            if payload['on']:
                if 'bri' not in payload or payload['bri'] == 0:
                    payload['bri'] = 100
            else:
                if 'bri' not in payload or payload['bri'] != 0:
                    payload['bri'] = 0
        HueGenericDevice.set_state(self, id, payload)

class HueColorDevice(HueDimDevice):

    def __init__(self,name):
        HueDimDevice.__init__(self,name)
        self.hascolor = True

class HueDimmableDevice(HueDimDevice):

    TYPE = "Dimmable light"
    # PRODUCT_NAME = "Generic dimmable light"
    MODEL_ID = "GDL-001"

    def __init__(self,name):
        HueDimDevice.__init__(self,name)

class HueSwitchDevice(HueGenericDevice):

    TYPE = "Switch light"
    # PRODUCT_NAME = "Generic dimmable light"
    MODEL_ID = "SL-001"

    def __init__(self, name):
        HueGenericDevice.__init__(self,name)
        self.type = HueSwitchDevice.TYPE
        self.modelid = HueSwitchDevice.MODEL_ID
        # self.productname = product_name

class HueExtendedColorDevice(HueColorDevice):

    TYPE = "Extended color light"
    # PRODUCT_NAME = "E4"
    MODEL_ID = "ECL-001"

    def __init__(self, name):
        HueColorDevice.__init__(self,name)
        self.type = HueExtendedColorDevice.TYPE
        self.modelid = HueExtendedColorDevice.MODEL_ID
        # self.productname = HueExtendedColorDevice.PRODUCT_NAME
        self.state['colormode'] = 'hs'
        self.state['hue'] = 0
        self.state['sat'] = 0
        
class HueXyColorDevice(HueColorDevice):

    TYPE = "XY color light"
    # PRODUCT_NAME = "E4"
    MODEL_ID = "XYL-001"

    def __init__(self, name):
        HueColorDevice.__init__(self,name)
        self.type = HueXyColorDevice.TYPE
        self.modelid = HueXyColorDevice.MODEL_ID
        # self.productname = HueXyColorDevice.PRODUCT_NAME
        self.state['colormode'] = 'xy'
        self.state['xy'] = [0.0,0.0]

class HueColorTemperatureDevice(HueColorDevice):

    TYPE = "Color Temperature light"
    # PRODUCT_NAME = "E4"
    MODEL_ID = "CTL-001"

    def __init__(self, name):
        HueColorDevice.__init__(self,name)
        self.type = HueColorTemperatureDevice.TYPE
        self.modelid = HueColorTemperatureDevice.MODEL_ID
        #self.productname = HueColorTemperatureDevice.PRODUCT_NAME
        self.state['colormode'] = 'ct'
        self.state['ct'] = 0
