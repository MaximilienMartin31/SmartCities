from time import sleep_ms

class LCD1602:
    def __init__(self, i2c, rows, cols, addr=0x3E):
        self.i2c = i2c
        self.addr = addr
        self.rows = rows
        self.cols = cols
        self.init_lcd()

    def init_lcd(self):
        sleep_ms(50)
        self.command(0x38)  # Function set
        self.command(0x39)  # IS=1
        self.command(0x14)
        self.command(0x70)
        self.command(0x56)
        self.command(0x6C)
        sleep_ms(200)
        self.command(0x38)
        self.command(0x0C)
        self.command(0x01)
        sleep_ms(2)

    def command(self, cmd):
        self.i2c.writeto(self.addr, bytes([0x00, cmd]))

    def write_char(self, char):
        self.i2c.writeto(self.addr, bytes([0x40, char]))

    def print(self, text):
        for c in text:
            self.write_char(ord(c))

    def clear(self):
        self.command(0x01)
        sleep_ms(2)

    def setCursor(self, col, row):
        addr = 0x80 + (0x40 * row + col)
        self.command(addr)

    def display(self):
        self.command(0x0C)

    def scrollDisplayLeft(self):
        self.command(0x18)

