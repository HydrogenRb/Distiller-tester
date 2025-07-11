import openpyxl
from openpyxl import Workbook, load_workbook
import os
import sys
import logging
import time
from datetime import datetime
import shutil
import subprocess
import serial.tools.list_ports

EXCEL_FILE = "pcb_test_results.xlsx"
SCORE_ITEMS = {
    "Fla1": 0, "Fla2": 0, "UART1": 0, "LED1": 0, "LED2": 0, "LED3": 0, "LED4": 0,
    "SD1": 0, "Hub1": 0, "Hub2": 0, "Eink1": 0, "Eink2": 0, "Aud1": 0, "Aud2": 0,
    "Pic1": 0, "Pow1": 0, "Bat1": 0, "Bat2": 0, "PD1": 0
}
ID_RANGE = range(1, 161)


# ---------- log system ----------
log_filename = f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[
        logging.FileHandler(log_filename, mode='w')
        #,logging.StreamHandler(sys.stdout)
    ]
)

# ---------- 重定向 print ----------
class LoggerWriter:
    def __init__(self, level, stream):
        self.level = level
        self.stream = stream

    def write(self, message):
        if message and message != '\n':
            self.level(message)
            self.stream.write(message)
            self.stream.flush()

    def flush(self):
        self.stream.flush()

sys.stdout = LoggerWriter(logging.info, sys.__stdout__)
sys.stderr = LoggerWriter(logging.error, sys.__stderr__)

# ---------- 清屏 ----------
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def logged_input(prompt=""):
    # 打印提示语到终端
    logging.info(f"[Prompt] {prompt.strip()}")
    sys.__stdout__.write(prompt)
    sys.__stdout__.flush()
    user_input = sys.stdin.readline().rstrip('\n')
    logging.info(f"[User Input] {user_input}")
    return user_input

def init_excel_file():
    if not os.path.exists(EXCEL_FILE):
        wb = Workbook()
        ws = wb.active
        ws.title = "TestResults"
        headers = ["BoardID"] + list(SCORE_ITEMS.keys())
        ws.append(headers)
        for i in ID_RANGE:
            ws.append([i] + [None]*len(SCORE_ITEMS))
        wb.save(EXCEL_FILE)

def load_excel():
    return load_workbook(EXCEL_FILE)

def get_board_row(ws, board_id):
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=1):
        if row[0].value == board_id:
            return row[0].row
    return None

def prompt_board_id():
    while True:
        try:
            board_id = int(logged_input(f"Board ID（{ID_RANGE.start}-{ID_RANGE.stop-1}）:"))
            if board_id in ID_RANGE:
                wb = load_excel()
                ws = wb["TestResults"]
                row_num = get_board_row(ws, board_id)
                if row_num:
                    tested = any(ws.cell(row=row_num, column=col).value is not None for col in range(2, 2 + len(SCORE_ITEMS)))
                    if tested:
                        print("[Warning] This board ID has already been tested. Please enter a new ID.\n")
                    else:
                        return board_id
            else:
                print("[Warning] ID over range, Please enter a new ID\n")
        except ValueError:
            print("[Warning] 输入无效，请输入数字。\n")

def run_tests_debug():
    print("请依次输入每项测试是否通过（1=通过，0=未通过）：\n")
    SAM_BOOT()
    items = list(SCORE_ITEMS.keys())
    print(f"当前测试项数量: {len(items)}")
    for item in items:
        while True:
            val = logged_input(f"{item}: ")
            if val in ("0", "1"):
                SCORE_ITEMS[item] = int(val)
                break
            else:
                print("请输入0或1。")
    return SCORE_ITEMS

# ---------- 测试辅助function ----------
def is_rp2040_connected():
    drives = [d.device for d in os.scandir('/mnt') if d.is_dir()] if os.name != 'nt' else [f"{chr(i)}:\\" for i in range(65,91) if os.path.exists(f"{chr(i)}:\\")]
    for drive in drives:
        if os.path.exists(os.path.join(drive, "INFO_UF2.txt")):
            return True
    return False

def find_rp2040_drive():
    if os.name == 'nt':
        drives = [f"{chr(i)}:\\" for i in range(65, 91) if os.path.exists(f"{chr(i)}:\\")]
    else:
        drives = [d.path for d in os.scandir('/mnt') if d.is_dir()]
    for drive in drives:
        if os.path.exists(os.path.join(drive, "INFO_UF2.txt")):
            return drive
    return None

# ------ 测试指令 ------
def SAM_BOOT():
    print("\n====================-----=====-----=====-----====================\n")
    print("Please hold down the SAM-BOOT button and then connect the device with a USB cable.\n")
    print("====================-----=====-----=====-----====================\n\n")
    print("Waiting for RP2040 device connection...\n")
    timeout = 30
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_rp2040_connected():
            print("Detected RP2040 device.\n")
            break
        time.sleep(1)
    else:
        print("[Warning] Not found RP2040 device in past 30s. Please check the connection and try again.\n")

def Nuke_RP2040():
    drive = find_rp2040_drive()
    uf2_path = "./ULP/flash_nuke.uf2"
    if drive and os.path.exists(uf2_path):
        try:
            shutil.copy(uf2_path, os.path.join(drive, "flash_nuke.uf2"))
            print("flash_nuke.uf2 uploaded successfully.")
        except Exception as e:
            print(f"[Error] Failed to upload UF2: {e}")
    else:
        print("[Error] RP2040 device not found or UF2 file missing.")

    print("Waiting for RP2040 device to reconnect...\n")
    timeout = 30
    start_time = time.time()
    time.sleep(3)
    while time.time() - start_time < timeout:
        drive = find_rp2040_drive()
        if drive:
            uf2_new_path = "./ULP/RPI_PICO-20240222-v1.22.2.uf2"
            if os.path.exists(uf2_new_path):
                try:
                    shutil.copy(uf2_new_path, os.path.join(drive, "RPI_PICO-20240222-v1.22.2.uf2"))
                    print("RPI_PICO-20240222-v1.22.2.uf2 uploaded successfully.\n")
                except Exception as e:
                    print(f"[Error] Failed to upload new UF2: {e}\n")
            else:
                print("[Error] New UF2 file missing.\n")
            break
        time.sleep(1)
    else:
        print("[Warning] RP2040 device not found for new UF2 upload in past 30s.")

def RP2040_upload():
    # 等待 mpremote 能找到设备
    timeout = 30
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            result = subprocess.run(
                ["mpremote", "connect", "list"],
                capture_output=True, text=True
            )
            if "Board" in result.stdout or "rp2" in result.stdout or "Microsoft" in result.stdout:
                print("mpremote 设备已连接。\n")
                break
        except Exception as e:
            print(f"[Error] 检查 mpremote 设备时出错: {e}\n")
        time.sleep(1)
    else:
        print("[Warning] 30秒内未检测到 mpremote 设备，请检查连接。\n")
        return

    time.sleep(2)
    src_dir = "./debugBHV0.2.3/"
    if os.path.exists(src_dir):
        for filename in os.listdir(src_dir):
            src_file = os.path.join(src_dir, filename)
            if os.path.isfile(src_file):
                try:
                    cmd = [
                        "mpremote", "fs", "cp", src_file, f":/{filename}"
                    ]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        print(f"{filename} uploaded successfully via mpremote.\n")
                    else:
                        print(f"[Error] mpremote failed for {filename}: {result.stderr}\n")
                except Exception as e:
                    print(f"[Error] Failed to upload {filename} via mpremote: {e}\n")
    else:
        print("[Error] Source directory missing.\n")

def Insert_CM5_test():
    clear_screen()
    print("\n====================-----=====-----=====-----====================\n")
    print("Unplug\n")
    print("Please insert the CM5 module into the board.\n")
    print("Hold the CM5-boot and plug USB.\n")
    print("====================-----=====-----=====-----====================\n\n")
    time.sleep(3)
    print("\n+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n")
    result = logged_input("Check if the Eink flash and display images (y/n): ").strip().lower()
    if result == 'y':
        SCORE_ITEMS["Fla1"] = 1
        SCORE_ITEMS["Eink1"] = 1
        print("Eink and flash test passed.\n")
    else:
        SCORE_ITEMS["Fla1"] = 0nn
        SCORE_ITEMS["Eink1"] = 0
        print("Eink and flash test failed.\n")

def check_LED():
    """
    检查LED灯状态。
    LED1: top front LED
    LED2: side front LED
    """
    clear_screen()
    print("\n==================== LED 检查 ====================\n")
    print("请观察板子上的LED灯状态：")
    print("  - LED1: 顶部前方的LED")
    print("  - LED2: 侧面前方的LED\n")
    print("请依次点亮LED1和LED2，并根据实际情况输入结果。")
    print("--------------------------------------------------\n")
    time.sleep(1)

    led1 = logged_input("LED1 (top front) 是否正常点亮？(y/n): ").strip().lower()
    if led1 == 'y':
        SCORE_ITEMS["LED1"] = 1
        print("LED1 检查通过。\n")
    else:
        SCORE_ITEMS["LED1"] = 0
        print("LED1 检查未通过。\n")

    led2 = logged_input("LED2 (side front) 是否正常点亮？(y/n): ").strip().lower()
    if led2 == 'y':
        SCORE_ITEMS["LED2"] = 1
        print("LED2 检查通过。\n")
    else:
        SCORE_ITEMS["LED2"] = 0
        print("LED2 检查未通过。\n")

    print("LED 检查完成。\n")


def CM5_flash_test():
    print("CM5 Flash Test, auto\n")
    time.sleep(2)
    # 运行 rpiboot.exe
    rpiboot_path = os.path.join(os.path.dirname(__file__), "rpiboot.exe")
    if not os.path.exists(rpiboot_path):
        print("[Error] 未找到 rpiboot.exe，请确保其在当前文件夹下。\n")
        SCORE_ITEMS["CM5Flash"] = 0
        return

    try:
        print("正在运行 rpiboot.exe，请稍候...\n")
        proc = subprocess.Popen([rpiboot_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # 等待一段时间让 rpiboot 完成
        time.sleep(8)
        proc.terminate()
    except Exception as e:
        print(f"[Error] 启动 rpiboot.exe 失败: {e}\n")
        SCORE_ITEMS["CM5Flash"] = 0
        return

    # 检查是否有新的U盘（CM5）出现
    print("正在检测新的U盘设备...\n")
    found_cm5 = False
    for _ in range(10):
        # Windows下，U盘通常会分配盘符D:~Z:
        for drive_letter in "DEFGHIJKLMNOPQRSTUVWXYZ":
            drive = f"{drive_letter}:\\"
            if os.path.exists(drive):
                try:
                    # 检查卷标或内容
                    if os.path.isdir(drive):
                        # 可以进一步检查卷标或文件特征
                        found_cm5 = True
                        break
                except Exception:
                    continue
        if found_cm5:
            break
        time.sleep(1)

    if found_cm5:
        print("检测到新的CM5 U盘设备，Flash测试通过。\n")
        SCORE_ITEMS["CM5Flash"] = 1
    else:
        print("[Error] 未检测到CM5 U盘设备，Flash测试失败。\n")
        SCORE_ITEMS["CM5Flash"] = 0

def reboot_rp2040():
    """
    通过向RP2040的串口发送1200bps触发重启（进入bootloader模式）。
    需要pyserial库。
    """
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("[Error] 未检测到任何串口设备，无法重启RP2040。\n")
        return False

    for port in ports:
        try:
            # 打开串口，设置波特率为1200
            ser = serial.Serial(port.device, 1200)
            ser.close()
            print(f"已向 {port.device} 发送1200bps重启信号。\n")
            # 通常RP2040会断开并重新枚举为USB存储设备
            time.sleep(2)
            return True
        except Exception as e:
            continue

    print("[Error] 未能成功重启任何RP2040串口设备。\n")
    return False

def run_tests():

    for key in SCORE_ITEMS:
        SCORE_ITEMS[key] = 0

    print("Init the Score board...\n")
    items = list(SCORE_ITEMS.keys())
    print(f"Number of test: {len(items)}")
    SAM_BOOT()
    Nuke_RP2040()
    RP2040_upload()
    #reboot_rp2040()
    #Insert_CM5_test()
    #check_LED()
    
    #CM5_flash_test()
    
    return SCORE_ITEMS

def save_results(wb, ws, board_id, results):
    row_num = get_board_row(ws, board_id)
    if row_num:
        for idx, key in enumerate(SCORE_ITEMS.keys(), start=2):
            ws.cell(row=row_num, column=idx, value=results[key])
        wb.save(EXCEL_FILE)
        print(f"Board ID {board_id} saved.")
    else:
        print("[error] Not found board ID in the Excel file.")

def main():
    init_excel_file()
    wb = load_excel()
    ws = wb["TestResults"]
    while True:
        #board_id = prompt_board_id()
        #results = run_tests_debug()
        save_results(wb, ws, prompt_board_id(), run_tests())
        cont = logged_input("Keep test (y/n): ").strip().lower()
        if cont != 'y':
            print("Testing completed.")
            break

if __name__ == "__main__":
    main()
