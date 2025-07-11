import machine
import struct

class BatteryManagementSystem:
    def __init__(self, address=0x55):
        self.i2c = machine.I2C(0, sda=machine.Pin(24), scl=machine.Pin(25))
        self.address = address

    def read_register(self, register, length):
        return self.i2c.readfrom_mem(self.address, register, length)

    def read_word(self, register):
        data = self.read_register(register, 2)
        return struct.unpack('<h', data)[0]

    def write_word(self, register, data):
        data = struct.pack('<H', data)
        self.i2c.writeto_mem(self.address, register, data)

    def print_formatted(self, label, value, unit):
        print(f"{label}: {value} {unit}")

    def get_control(self):
        value = self.read_word(0x00)
        self.print_formatted("Control", value, "")

    def get_temperature(self):
        value = self.read_word(0x02) * 0.1  # 单位是 0.1K
        self.print_formatted("Temperature", value - 273.15, "°C")

    def get_voltage(self):
        value = self.read_word(0x04) / 1000.0  # 转换成 V
        #self.print_formatted("Voltage", value, "V")
        return value

    def get_current(self):
        value = self.read_word(0x10)  # 有正负值，单位 mA
        #self.print_formatted("Current", value, "mA")
        return float(value)

    def get_remaining_capacity(self):
        value = self.read_word(0x0C)
        #self.print_formatted("Remaining Capacity", value, "mAh")
        return float(value)

    def get_state_of_charge(self):
        value = self.read_word(0x1C)
        #self.print_formatted("State of Charge", value, "%")
        return float(value)
