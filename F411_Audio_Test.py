import serial
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import time
from collections import deque
import struct

class AudioMonitor:
    def __init__(self, port='COM16', baudrate=921600):
        self.ser = serial.Serial(port, baudrate)
        self.data_buffer = deque(maxlen=5000)  # 存儲最近的5000個樣本
        self.time_buffer = deque(maxlen=100)   # 存儲時間戳
        self.frame_count = 0
        self.error_count = 0
        
        # 創建圖形
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(10, 8))
        self.line1, = self.ax1.plot([], [], 'b-', label='Audio Data')
        self.line2, = self.ax2.plot([], [], 'g-', label='Frame Rate')
        
        # 設置圖形屬性
        self.ax1.set_title('Audio Waveform')
        self.ax1.set_ylim(-2048, 2048)
        self.ax1.grid(True)
        self.ax1.legend()
        
        self.ax2.set_title('Frame Rate')
        self.ax2.set_ylim(0, 50)
        self.ax2.grid(True)
        self.ax2.legend()
        
        plt.tight_layout()

    def read_frame(self):
        # 等待幀頭
        while True:
            if self.ser.read() == b'\xAA' and self.ser.read() == b'\x55':
                break

        # 讀取數據長度
        size_bytes = self.ser.read(2)
        size = struct.unpack('<H', size_bytes)[0]

        if size != 512:  # 預期的 FRAME_SIZE
            self.error_count += 1
            return None

        # 讀取音頻數據
        data_bytes = self.ser.read(size * 2)  # 每個樣本 2 bytes
        checksum_bytes = self.ser.read(2)
        
        # 解析數據
        audio_data = np.frombuffer(data_bytes, dtype=np.int16)
        received_checksum = struct.unpack('<H', checksum_bytes)[0]
        
        # 驗證校驗和
        calc_checksum = np.sum(audio_data) & 0xFFFF
        
        if calc_checksum != received_checksum:
            self.error_count += 1
            return None
            
        return audio_data

    def update_plot(self, frame):
        try:
            # 讀取一幀數據
            data = self.read_frame()
            if data is not None:
                # 更新音頻數據
                self.data_buffer.extend(data)
                self.frame_count += 1
                
                # 計算幀率
                current_time = time.time()
                self.time_buffer.append(current_time)
                
                if len(self.time_buffer) > 1:
                    time_diff = current_time - self.time_buffer[0]
                    if time_diff > 0:
                        frame_rate = len(self.time_buffer) / time_diff
                        self.ax2.set_title(f'Frame Rate: {frame_rate:.1f} fps')

                # 更新波形圖
                self.line1.set_data(range(len(self.data_buffer)), list(self.data_buffer))
                self.ax1.set_xlim(0, len(self.data_buffer))
                
                # 更新幀率圖
                x_time = np.linspace(0, len(self.time_buffer), len(self.time_buffer))
                frame_rates = [i/(j-self.time_buffer[0]) for i, j in enumerate(self.time_buffer)][1:]
                self.line2.set_data(x_time[1:], frame_rates)
                self.ax2.set_xlim(0, len(self.time_buffer))

                # 顯示統計信息
                self.ax1.set_title(f'Audio Waveform (Frames: {self.frame_count}, Errors: {self.error_count})')

            return self.line1, self.line2

        except Exception as e:
            print(f"Error: {e}")
            return self.line1, self.line2

    def start(self):
        # 發送任意字符以觸發STM32開始發送
        self.ser.write(b'start\n')
        
        # 創建動畫
        self.ani = FuncAnimation(self.fig, self.update_plot, interval=50,
                               blit=True)
        plt.show()

    def stop(self):
        self.ser.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Audio Monitor')
    parser.add_argument('--port', type=str, default='COM16', help='Serial port')
    parser.add_argument('--baudrate', type=int, default=921600, help='Baudrate')
    
    args = parser.parse_args()
    
    print(f"Starting Audio Monitor on {args.port} at {args.baudrate} baud")
    
    monitor = AudioMonitor(port=args.port, baudrate=args.baudrate)
    try:
        monitor.start()
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        monitor.stop()
