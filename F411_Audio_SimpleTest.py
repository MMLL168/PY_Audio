import serial
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque
import time

class SimpleAudioTest:
    def __init__(self, port='COM16', baudrate=921600):
        # 基本初始化
        print("初始化中...")
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.connect_serial()
        
        # 數據緩衝
        self.data_buffer = deque(maxlen=1000)
        
        # 創建圖表
        self.fig, self.ax = plt.subplots()
        self.line, = self.ax.plot([], [])
        self.ax.set_ylim(-2000, 2000)
        
    def connect_serial(self):
        """連接串口"""
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1
            )
            print(f"成功連接到串口 {self.port}")
            # 新增：顯示串口配置
            print(f"串口配置:")
            print(f"- 波特率: {self.ser.baudrate}")
            print(f"- 數據位: {self.ser.bytesize}")
            print(f"- 校驗位: {self.ser.parity}")
            print(f"- 停止位: {self.ser.stopbits}")
        except Exception as e:
            print(f"串口連接失敗: {e}")
            raise
    
    def read_data(self):
        """讀取數據"""
        try:
            if self.ser and self.ser.in_waiting:
                print(f"可讀取的數據量: {self.ser.in_waiting} bytes")  # 新增：顯示可讀取的數據量
                
                # 尋找幀頭
                while True:
                    if self.ser.read() == b'\xAA' and self.ser.read() == b'\x55':
                        print("找到幀頭 AA 55")  # 新增：確認幀頭
                        break
                
                # 讀取數據長度
                length_bytes = self.ser.read(2)
                length = int.from_bytes(length_bytes, 'little')
                print(f"數據長度: {length}")  # 新增：顯示數據長度
                
                # 讀取數據
                data_bytes = self.ser.read(length * 2)
                if len(data_bytes) == length * 2:
                    data = []
                    for i in range(0, len(data_bytes), 2):
                        value = int.from_bytes(data_bytes[i:i+2], 'little')
                        if value > 32767:
                            value -= 65536
                        data.append(value)
                    return data
                else:
                    print(f"數據長度不符: 期望 {length * 2}, 實際 {len(data_bytes)}")  # 新增：數據長度檢查
        except Exception as e:
            print(f"讀取數據時出錯: {e}")
        return None

    def update(self, frame):
        """更新圖表"""
        data = self.read_data()
        if data:
            self.data_buffer.extend(data)
            print(f"接收到 {len(data)} 個數據點")
            
        # 更新圖表
        self.line.set_data(range(len(self.data_buffer)), self.data_buffer)
        self.ax.set_xlim(0, len(self.data_buffer))
        return self.line,

    def start(self):
        """開始運行"""
        print("開始運行...")
        self.ani = FuncAnimation(
            self.fig, 
            self.update, 
            interval=20,
            blit=True
        )
        plt.show()

    def __del__(self):
        """清理資源"""
        if hasattr(self, 'ser') and self.ser:
            self.ser.close()
            print("串口已關閉")

if __name__ == "__main__":
    # 列出所有可用串口
    print("檢查可用串口...")
    import serial.tools.list_ports
    ports = list(serial.tools.list_ports.comports())
    print("可用的串口:")
    for p in ports:
        print(f"- {p}")
    
    # 確認 Python 版本和套件
    import sys
    print(f"\nPython 版本: {sys.version}")
    
    try:
        # 創建測試實例
        print("\n創建測試實例...")
        test = SimpleAudioTest(port='COM16')  # 使用 COM16
        
        # 開始測試
        print("\n開始測試...")
        test.start()
        
    except Exception as e:
        print(f"\n程序出錯: {e}")
    finally:
        input("\n按Enter鍵退出...")
