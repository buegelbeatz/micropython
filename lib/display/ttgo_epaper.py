from machine import SPI, Pin
from . import DEPG0213BN as epaper

# TODO: not tested yet 
# https://github.com/Inqbus/micropython_DEPG0213BN

class TTGOEpaper(epaper.EPD):

    def __init__(self):

        # Setup SPI bus. The pins are mandatory for the TTGO T5 V2.3
        espi = SPI(2,
                baudrate=4000000,
                sck=Pin(18),
                mosi=Pin(23),
                polarity=0,
                phase=0,
                firstbit=SPI.MSB)

        # The pins a mandatory for the TTGO T5 V2.3
        rst = Pin(16, Pin.OUT, value=1)
        dc = Pin(17, Pin.OUT, value=1)
        cs = Pin(5, Pin.OUT, value=1)
        busy = Pin(4, Pin.IN, value=0)

        # Instantiate a Screen
        super().__init__(espi, cs, dc, rst, busy, rotation=epaper.ROTATION_90)
        # # Set all to white
        # screen.fill(1)
        # # Write at (0,0) the text "hello World!" in color black
        # screen.text('Hello World!', 0, 0, 0)
        # # Write to the E-Ink display
        # screen.update()
