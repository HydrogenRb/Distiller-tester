#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
质检脚本 - 用于检查板子功能
"""

import os
import sys
import time
import subprocess
import paramiko
from datetime import datetime

class QualityChecker:
    def __init__(self):
        self.board_id = None
        self.results = {
            'screen': 0,
            'rp2040': 0,
            'sd_card': 0,
            'camera': 0,
            'audio': 0
        }
        self.ssh_client = None
        
    def get_board_id(self):
        """获取板子ID"""
        print("=" * 50)
        print("质检脚本启动")
        print("=" * 50)
        self.board_id = input("请输入板子的ID: ").strip()
        if not self.board_id:
            print("错误：板子ID不能为空")
            sys.exit(1)
        print(f"板子ID: {self.board_id}")
        
    def check_screen(self):
        """第一步：检查屏幕"""
        print("\n" + "=" * 30)
        print("第一步：检查屏幕")
        print("=" * 30)
        
        while True:
            response = input("屏幕是好的吗？(y/n): ").strip().lower()
            if response in ['y', 'yes', '是']:
                self.results['screen'] = 1
                print("✓ 屏幕检查通过")
                break
            elif response in ['n', 'no', '否']:
                self.results['screen'] = 0
                print("✗ 屏幕检查失败")
                break
            else:
                print("请输入 y 或 n")
                
    def connect_raspberry_pi(self):
        """第二步：连接树莓派"""
        print("\n" + "=" * 30)
        print("第二步：连接树莓派")
        print("=" * 30)
        
        print("正在连接树莓派...")
        max_attempts = 5
        attempt = 1
        
        while attempt <= max_attempts:
            try:
                print(f"尝试连接 {attempt}/{max_attempts}...")
                self.ssh_client = paramiko.SSHClient()
                self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.ssh_client.connect(
                    '192.168.0.235',
                    username='distiller',
                    password='one',
                    timeout=10
                )
                print("✓ 成功连接到树莓派")
                return True
            except Exception as e:
                print(f"连接失败: {e}")
                if attempt < max_attempts:
                    print("等待5秒后重试...")
                    time.sleep(5)
                attempt += 1
                
        print("✗ 无法连接到树莓派")
        return False
        
    def check_rp2040(self):
        """第三步：检查RP2040访问"""
        print("\n" + "=" * 30)
        print("第三步：检查RP2040访问")
        print("=" * 30)
        
        if not self.ssh_client:
            print("✗ SSH连接未建立")
            self.results['rp2040'] = 0
            return
            
        try:
            stdin, stdout, stderr = self.ssh_client.exec_command('lsusb')
            output = stdout.read().decode('utf-8')
            print("USB设备列表:")
            print(output)
            
            if 'MicroPython Board in FS mode' in output:
                self.results['rp2040'] = 1
                print("✓ 找到MicroPython Board in FS mode")
            else:
                self.results['rp2040'] = 0
                print("✗ 未找到MicroPython Board in FS mode")
                
        except Exception as e:
            print(f"✗ 检查RP2040失败: {e}")
            self.results['rp2040'] = 0
            
    def check_sd_card(self):
        """第四步：检查SD卡"""
        print("\n" + "=" * 30)
        print("第四步：检查SD卡")
        print("=" * 30)
        
        if not self.ssh_client:
            print("✗ SSH连接未建立")
            self.results['sd_card'] = 0
            return
            
        try:
            stdin, stdout, stderr = self.ssh_client.exec_command('lsblk')
            output = stdout.read().decode('utf-8')
            print("块设备列表:")
            print(output)
            
            if '59.5G' in output:
                self.results['sd_card'] = 1
                print("✓ 找到59.5G设备")
            else:
                self.results['sd_card'] = 0
                print("✗ 未找到59.5G设备")
                
        except Exception as e:
            print(f"✗ 检查SD卡失败: {e}")
            self.results['sd_card'] = 0
            
    def check_camera(self):
        """第五步：检查摄像头"""
        print("\n" + "=" * 30)
        print("第五步：检查摄像头")
        print("=" * 30)
        
        if not self.ssh_client:
            print("✗ SSH连接未建立")
            self.results['camera'] = 0
            return
            
        try:
            # 进入指定目录
            stdin, stdout, stderr = self.ssh_client.exec_command('cd ~/testForBHV023 && pwd')
            output = stdout.read().decode('utf-8').strip()
            print(f"当前目录: {output}")
            
            # 询问用户是否拍照
            while True:
                response = input("是否开始拍照？(y/n): ").strip().lower()
                if response in ['y', 'yes', '是']:
                    break
                elif response in ['n', 'no', '否']:
                    print("跳过拍照步骤")
                    self.results['camera'] = 0
                    return
                else:
                    print("请输入 y 或 n")
            
            # 拍照
            photo_filename = f"test_{self.board_id}.jpg"
            cmd = f'cd ~/testForBHV023 && libcamera-still -o {photo_filename}'
            print(f"执行命令: {cmd}")
            
            stdin, stdout, stderr = self.ssh_client.exec_command(cmd, timeout=30)
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status == 0:
                self.results['camera'] = 1
                print("✓ 拍照成功")
            else:
                error = stderr.read().decode('utf-8')
                print(f"✗ 拍照失败: {error}")
                self.results['camera'] = 0
                
        except Exception as e:
            print(f"✗ 检查摄像头失败: {e}")
            self.results['camera'] = 0
            
    def record_audio(self):
        """第六步：录音"""
        print("\n" + "=" * 30)
        print("第六步：录音")
        print("=" * 30)
        
        if not self.ssh_client:
            print("✗ SSH连接未建立")
            self.results['audio'] = 0
            return
            
        try:
            audio_filename = f"test_{self.board_id}.wav"
            # 自动检测可用的录音设备（hw:1,0 或 hw:0,0）
            # 先尝试hw:1,0，如果失败再尝试hw:0,0
            arecord_device = "hw:1,0"
            # 检查hw:1,0是否存在
            try:
                check_cmd = "arecord -l"
                stdin, stdout, stderr = self.ssh_client.exec_command(check_cmd)
                card_list = stdout.read().decode('utf-8')
                if "card 1:" not in card_list:
                    arecord_device = "hw:0,0"
            except Exception as e:
                print(f"检测录音设备时出错: {e}")
                arecord_device = "hw:0,0"
            cmd = f'cd ~/testForBHV023 && arecord -D {arecord_device} -f S32_LE -c 2 -r 48000 -d 3 {audio_filename}'
            print(f"执行录音命令: {cmd}")
            print("录音中... (5秒)")
            
            stdin, stdout, stderr = self.ssh_client.exec_command(cmd, timeout=10)
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status == 0:
                self.results['audio'] = 1
                print("✓ 录音成功")
            else:
                error = stderr.read().decode('utf-8')
                print(f"✗ 录音失败: {error}")
                self.results['audio'] = 0
                
        except Exception as e:
            print(f"✗ 录音失败: {e}")
            self.results['audio'] = 0
            
    def transfer_files(self):
        """第七步：传输文件到本地"""
        print("\n" + "=" * 30)
        print("第七步：传输文件到本地")
        print("=" * 30)
        
        if not self.ssh_client:
            print("✗ SSH连接未建立")
            return
            
        try:
            # 创建SFTP客户端
            sftp = self.ssh_client.open_sftp()
            
            # 获取用户主目录的绝对路径
            stdin, stdout, stderr = self.ssh_client.exec_command('echo $HOME')
            home_dir = stdout.read().decode('utf-8').strip()
            
            # 传输照片
            remote_photo = f"{home_dir}/testForBHV023/test_{self.board_id}.jpg"
            local_photo = f"test_{self.board_id}.jpg"
            
            print(f"传输照片: {remote_photo} -> {local_photo}")
            sftp.get(remote_photo, local_photo)
            print("✓ 照片传输成功")
            
            # 传输音频
            remote_audio = f"{home_dir}/testForBHV023/test_{self.board_id}.wav"
            local_audio = f"test_{self.board_id}.wav"
            
            print(f"传输音频: {remote_audio} -> {local_audio}")
            sftp.get(remote_audio, local_audio)
            print("✓ 音频传输成功")
            
            sftp.close()
            
        except Exception as e:
            print(f"✗ 文件传输失败: {e}")
            
    def open_files(self):
        """打开图片和音频文件"""
        print("\n" + "=" * 30)
        print("打开文件")
        print("=" * 30)
        
        photo_file = f"test_{self.board_id}.jpg"
        audio_file = f"test_{self.board_id}.wav"
        
        # 打开图片
        if os.path.exists(photo_file):
            try:
                if sys.platform.startswith('win'):
                    # Windows
                    os.startfile(photo_file)
                elif sys.platform.startswith('darwin'):
                    # macOS
                    subprocess.run(['open', photo_file], check=True)
                else:
                    # Linux
                    subprocess.run(['xdg-open', photo_file], check=True)
                print(f"✓ 已打开图片: {photo_file}")
            except Exception as e:
                print(f"✗ 打开图片失败: {e}")
        else:
            print(f"✗ 图片文件不存在: {photo_file}")
            
        # 打开音频
        if os.path.exists(audio_file):
            try:
                if sys.platform.startswith('win'):
                    # Windows
                    os.startfile(audio_file)
                elif sys.platform.startswith('darwin'):
                    # macOS
                    subprocess.run(['open', audio_file], check=True)
                else:
                    # Linux
                    subprocess.run(['xdg-open', audio_file], check=True)
                print(f"✓ 已打开音频: {audio_file}")
            except Exception as e:
                print(f"✗ 打开音频失败: {e}")
        else:
            print(f"✗ 音频文件不存在: {audio_file}")
            
    def check_files_quality(self):
        """检查文件质量"""
        print("\n" + "=" * 30)
        print("检查文件质量")
        print("=" * 30)
        
        photo_file = f"test_{self.board_id}.jpg"
        audio_file = f"test_{self.board_id}.wav"
        
        # 检查照片
        if os.path.exists(photo_file):
            photo_size = os.path.getsize(photo_file)
            print(f"照片文件大小: {photo_size} 字节")
            if photo_size > 0:
                # 自动打开图片
                self.open_files()
                
                while True:
                    response = input("照片质量是否OK？(y/n): ").strip().lower()
                    if response in ['y', 'yes', '是']:
                        self.results['camera'] = 1
                        break
                    elif response in ['n', 'no', '否']:
                        self.results['camera'] = 0
                        break
                    else:
                        print("请输入 y 或 n")
            else:
                print("✗ 照片文件为空")
                self.results['camera'] = 0
        else:
            print("✗ 照片文件不存在")
            self.results['camera'] = 0
            
        # 检查音频
        if os.path.exists(audio_file):
            audio_size = os.path.getsize(audio_file)
            print(f"音频文件大小: {audio_size} 字节")
            if audio_size > 0:
                while True:
                    response = input("音频质量是否OK？(y/n): ").strip().lower()
                    if response in ['y', 'yes', '是']:
                        self.results['audio'] = 1
                        break
                    elif response in ['n', 'no', '否']:
                        self.results['audio'] = 0
                        break
                    else:
                        print("请输入 y 或 n")
            else:
                print("✗ 音频文件为空")
                self.results['audio'] = 0
        else:
            print("✗ 音频文件不存在")
            self.results['audio'] = 0
            
    def save_results(self):
        """保存测试结果"""
        print("\n" + "=" * 30)
        print("保存测试结果")
        print("=" * 30)
        
        result_line = f"ID:{self.board_id} 屏幕:{self.results['screen']} 访问RP2040:{self.results['rp2040']} SD卡:{self.results['sd_card']} 摄像头:{self.results['camera']} 录音:{self.results['audio']}"
        
        try:
            with open('testresult.txt', 'a', encoding='utf-8') as f:
                f.write(result_line + '\n')
            print("✓ 结果已保存到 testresult.txt")
            print(f"结果: {result_line}")
        except Exception as e:
            print(f"✗ 保存结果失败: {e}")
            
    def cleanup(self):
        """清理资源"""
        if self.ssh_client:
            self.ssh_client.close()
            
    def run(self):
        """运行完整的质检流程"""
        try:
            self.get_board_id()
            self.check_screen()
            
            if not self.connect_raspberry_pi():
                print("无法连接到树莓派，跳过后续步骤")
                self.save_results()
                return
                
            self.check_rp2040()
            self.check_sd_card()
            self.check_camera()
            self.record_audio()
            self.transfer_files()
            self.check_files_quality()
            self.save_results()
            
        except KeyboardInterrupt:
            print("\n用户中断了测试")
        except Exception as e:
            print(f"测试过程中出现错误: {e}")
        finally:
            self.cleanup()

def main():
    """主函数"""
    while True:
        checker = QualityChecker()
        checker.run()
        
        print("\n" + "=" * 50)
        response = input("是否需要继续测试？(y/n): ").strip().lower()
        if response not in ['y', 'yes', '是']:
            print("测试结束")
            break

if __name__ == "__main__":
    main() 