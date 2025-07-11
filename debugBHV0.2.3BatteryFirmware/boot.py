# boot.py
import machine

if machine.Pin(16, machine.Pin.IN, machine.Pin.PULL_UP).value() == 0:
    print("Skip main.py")
else:
    import main
