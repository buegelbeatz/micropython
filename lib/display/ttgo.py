from . import st7789py as st7789
import machine
from .romfonts import vga2_8x16 as font

class TTGO(st7789.ST7789):

    # Color definitions
    BLACK = st7789.GREEN
    BLUE = st7789.GREEN
    RED = st7789.GREEN
    GREEN = st7789.GREEN
    CYAN = st7789.GREEN
    MAGENTA = st7789.GREEN
    YELLOW = st7789.GREEN
    WHITE = st7789.GREEN
    GREY = 0x1111

    def __init__(self):
        spi = machine.SoftSPI(
            baudrate=20000000,
            polarity=1,
            phase=0,
            sck=machine.Pin(18),
            mosi=machine.Pin(19),
            miso=machine.Pin(13))

        super().__init__(spi,
            135,
            240,
            reset=machine.Pin(23, machine.Pin.OUT),
            cs=machine.Pin(5, machine.Pin.OUT),
            dc=machine.Pin(16, machine.Pin.OUT),
            backlight=machine.Pin(4, machine.Pin.OUT),
            rotation=0)

    def text(self, text, x0, y0, color=st7789.GREEN, background=st7789.BLACK):
        super().text(font, text, x0, y0, color, background)

    def write(self, string, x, y, fg=st7789.WHITE, bg=st7789.BLACK):
        super().write( font, string, x, y, fg, bg)

    def write_width(self, string):
        return super().write_width(font, string)