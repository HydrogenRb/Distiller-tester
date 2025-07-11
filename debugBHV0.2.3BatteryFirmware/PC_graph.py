import serial
import time
import re

# 修改为你实际的串口号（Windows: COM3，Linux/macOS: /dev/ttyACM0 或 /dev/ttyUSB0）
PORT = 'COM70'      # 或 '/dev/ttyACM0'
BAUDRATE = 115200

def parse_line(line):
    line = line.strip()
    # 可选：解析格式，例如：Voltage: 5.10 V
    match = re.match(r"(\w[\w\s]+):\s*([-+]?\d*\.?\d+)\s*(\w*)", line)
    if match:
        label, value, unit = match.groups()
        print(f"{label:<25}: {value} {unit}")
    else:
        print(line)  # 未识别格式的原样输出

def main():
    try:
        with serial.Serial(PORT, BAUDRATE, timeout=1) as ser:
            print(f"[INFO] Connected to {PORT} at {BAUDRATE} baud.")
            print("[INFO] Waiting for data...\n")

            while True:
                try:
                    line = ser.readline().decode('utf-8', errors='ignore')
                    if line:
                        parse_line(line)
                except KeyboardInterrupt:
                    print("\n[INFO] Exiting...")
                    break
                except Exception as e:
                    print(f"[ERROR] {e}")
                    time.sleep(1)
    except serial.SerialException as e:
        print(f"[ERROR] Failed to open port {PORT}: {e}")

if __name__ == "__main__":
    main()
