# https://docs.micropython.org/en/latest/esp8266/tutorial/ssd1306.html

from machine import Pin, I2C
import ssd1306
import framebuf

# TODO: needs to be tested


class I2CDisplay(framebuf.FrameBuffer):

    def __init__(self):
        # using default address 0x3C
        i2c = I2C(sda=Pin(4), scl=Pin(5))
        ssd1306.SSD1306_I2C(128, 64, i2c)
        super().__init__()

    def demo(self):
        self.fill(0)
        self.fill_rect(0, 0, 32, 32, 1)
        self.fill_rect(2, 2, 28, 28, 0)
        self.vline(9, 8, 22, 1)
        self.vline(16, 2, 22, 1)
        self.vline(23, 8, 22, 1)
        self.fill_rect(26, 24, 2, 4, 1)
        self.text('MicroPython', 40, 0, 1)
        self.text('SSD1306', 40, 12, 1)
        self.text('OLED 128x64', 40, 24, 1)
        self.show()
