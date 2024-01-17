#from . import crypto
import json

class Environment():

    def __init__(self, filename="env.json"):
        self.filename = filename
        #self.crypto = crypto.Crypto()
        self.storage = self._read() 
        self._read()

    def __destroy__(self):
        self._write(self.storage)

    def save(self, data):
        return self._write(data)

    def _read(self):
        try:
            f = open(self.filename)
            data = f.read()
            f.close()
            #return json.loads(self.crypto.decrypt(data))
            return json.loads(data)
        except:
            pass   

    def _write(self, data):
        try:
            f = open(self.filename ,'w')
            f.write(json.dumps(data))
            #f.write(self.crypto.encrypt(json.dumps(data)))
            f.close()
        except:
            return False 
        return True