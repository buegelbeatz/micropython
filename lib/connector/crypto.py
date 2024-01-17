import machine
import ucryptolib
import ubinascii
import re

class Crypto():

    def __init__(self):
        _key = machine.unique_id()*3
        self.key = _key[:16]

    def encrypt(self, message):
        cipher = ucryptolib.aes(self.key, 1)
        plain_text = str(len(message)) + ':' + message 
        plain_text += " "*(16 - len(plain_text) % 16)
        return ubinascii.hexlify(cipher.encrypt(plain_text))

    def decrypt(self, message):
        cipher = ucryptolib.aes(self.key, 1)
        plain_text = ubinascii.unhexlify(cipher.decrypt(message)).decode()
        length = int(re.sub(':.*$','',plain_text))
        return re.sub('^[^:]*:','',plain_text)[0:length + 1]