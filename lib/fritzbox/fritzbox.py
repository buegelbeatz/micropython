# https://github.com/wilm02/wilm

import re
import json
import ubinascii
import uhashlib as hashlib

from ssdp.ssdp import Ssdp
from ssdp.hue_devices import HueDevice, HueDeviceType, HueDevices, hue_sat_to_rgb, rgb_to_hue_sat
from ssdp.tools import get_hex, load_from_path, get_mac, format_str, dict_exclude, date
from debugger import Debugger
import error

debug = Debugger(color_schema='green')
debug.active = True

class Fritzbox(Ssdp):

    _tcp_handler = []

