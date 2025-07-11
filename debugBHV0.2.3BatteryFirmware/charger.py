import machine

class CH224:
    def __init__(self, i2c=None, address=0x23):
        self.address = address
        if i2c:
            self.i2c = i2c
        else:
            # 默认使用 I2C0, SDA=24, SCL=25（根据你板子具体接法）
            self.i2c = machine.I2C(0, scl=machine.Pin(25), sda=machine.Pin(24))

    def read_register(self, register, length):
        return self.i2c.readfrom_mem(self.address, register, length)

    def read_word(self, register):
        data = self.read_register(register, 2)
        return struct.unpack('<h', data)[0]
    
    def read_byte(self, register):
        try:
            return int.from_bytes(self.i2c.readfrom_mem(self.address, register, 1), 'little')
        except Exception as e:
            print(f"Read error at register 0x{register:02X}: {e}")
            return 114

    def get_protocol(self):
        register = 0x09
        status = self.read_byte(0x09)
        #print(status)
        if status is None:
            return

        protocol_flags = {
            "BC": bool(status & 0x01),
            "QC2": bool(status & 0x02),
            "QC3": bool(status & 0x04),
            "PD": bool(status & 0x08),
            "EPR": bool(status & 0x10)
        }

        return(status)

    def get_PD(self):
        current_raw = self.read_byte(0x50)
        if current_raw is None:
            return 114
        current_ma = current_raw * 50
        return(current_ma)

# 使用示例
if __name__ == "__main__":
    pd = CH224()
    pd.get_protocol()
    pd.get_PD()
