import serial
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque
import time
from scipy import signal
from scipy.fft import fft
import librosa
import serial.tools.list_ports

class VoiceCommandDetector:
    def __init__(self, port='COM16', baudrate=921600):
        # 基本初始化
        print("初始化中...")
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.connect_serial()
        
        # 數據緩衝
        self.buffer_size = 2000
        self.data_buffer = deque(maxlen=self.buffer_size)
        
        # 創建圖表
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(10, 8))
        self.line1, = self.ax1.plot([], [], 'b-', label='波形')
        self.line2, = self.ax2.plot([], [], 'r-', label='頻譜')
        
        # 設置圖表屬性
        self.ax1.set_ylim(-2000, 2000)
        self.ax1.set_title('時域波形')
        self.ax1.grid(True)
        self.ax1.legend()
        
        self.ax2.set_title('頻譜')
        self.ax2.grid(True)
        self.ax2.legend()
        
        # 語音檢測參數
        self.energy_threshold = 1000
        self.word_detected = False
        self.silence_counter = 0
        self.recording = []
        
        # 狀態指示
        self.status_text = self.ax1.text(0.02, 0.95, '', 
                                       transform=self.ax1.transAxes,
                                       bbox=dict(facecolor='white', alpha=0.8))
        
    def connect_serial(self):
        """連接串口"""
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1
            )
            print(f"成功連接到串口 {self.port}")
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
                # 尋找幀頭
                while True:
                    if self.ser.read() == b'\xAA' and self.ser.read() == b'\x55':
                        break
                
                # 讀取數據長度
                length_bytes = self.ser.read(2)
                length = int.from_bytes(length_bytes, 'little')
                
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
        except Exception as e:
            print(f"讀取數據時出錯: {e}")
        return None

    def calculate_features(self, audio_data):
        """計算音頻特徵"""
        if len(audio_data) < 100:
            return None, None
            
        # 計算能量
        energy = np.mean(np.abs(audio_data))
        
        # 計算過零率
        zero_crossings = np.sum(np.abs(np.diff(np.signbit(audio_data))))
        
        return energy, zero_crossings

    def detect_keyword(self, audio_data):
        """關鍵詞檢測"""
        if len(audio_data) < 1000:
            return None
            
        energy, zero_crossings = self.calculate_features(audio_data)
        
        if energy is None:
            return None
            
        # 簡單的特徵匹配
        if energy > self.energy_threshold:
            if zero_crossings > 100:
                return "哈囉"
            else:
                return "你好"
                
        return None

    def update_status(self, status):
        """更新狀態顯示"""
        self.status_text.set_text(status)

    def update(self, frame):
        """更新圖表和處理語音"""
        data = self.read_data()
        if data:
            self.data_buffer.extend(data)
            
            # 檢測語音
            audio_array = np.array(list(self.data_buffer))
            current_energy = np.mean(np.abs(audio_array))
            
            # 更新狀態顯示
            status = f"能量: {current_energy:.0f}"
            
            if not self.word_detected and current_energy > self.energy_threshold:
                self.word_detected = True
                self.recording = []
                status += "\n檢測到語音"
                
            if self.word_detected:
                self.recording.extend(data)
                
                # 檢查是否結束
                if current_energy < self.energy_threshold:
                    self.silence_counter += 1
                    if self.silence_counter > 10:
                        self.word_detected = False
                        self.silence_counter = 0
                        
                        # 識別關鍵詞
                        keyword = self.detect_keyword(np.array(self.recording))
                        if keyword:
                            status += f"\n檢測到: {keyword}"
                else:
                    self.silence_counter = 0
            
            self.update_status(status)
            
            # 更新時域圖
            self.line1.set_data(range(len(self.data_buffer)), self.data_buffer)
            self.ax1.set_xlim(0, len(self.data_buffer))
            
            # 更新頻譜圖
            if len(self.data_buffer) > 100:
                spectrum = np.abs(fft(list(self.data_buffer)))
                freq = np.fft.fftfreq(len(spectrum))
                self.line2.set_data(freq[:len(freq)//2], spectrum[:len(spectrum)//2])
                self.ax2.set_xlim(0, 0.5)
                self.ax2.set_ylim(0, np.max(spectrum[:len(spectrum)//2]))
                
        return self.line1, self.line2

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

def main():
    # 列出所有可用串口
    print("檢查可用串口...")
    ports = list(serial.tools.list_ports.comports())
    print("可用的串口:")
    for p in ports:
        print(f"- {p}")
    
    try:
        # 創建檢測器實例
        detector = VoiceCommandDetector(port='COM16')
        
        # 開始檢測
        detector.start()
        
    except Exception as e:
        print(f"程序出錯: {e}")
    finally:
        input("按Enter鍵退出...")

if __name__ == "__main__":
    main()
