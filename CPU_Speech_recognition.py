import speech_recognition as sr
import sounddevice as sd
import numpy as np
import wave
import io

def record_audio(duration=5, sample_rate=44100):
    """直接使用 sounddevice 錄音"""
    print("開始錄音...")
    recording = sd.rec(int(duration * sample_rate),
                      samplerate=sample_rate,
                      channels=1,
                      dtype='int16')
    sd.wait()
    print("錄音完成")
    return recording, sample_rate

def save_audio_to_wav(recording, sample_rate):
    """將錄音數據保存為 WAV 格式"""
    byte_io = io.BytesIO()
    with wave.open(byte_io, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(recording.tobytes())
    return byte_io

def test_microphone():
    recognizer = sr.Recognizer()
    
    try:
        # 錄音
        recording, sample_rate = record_audio(duration=5)
        
        # 將錄音轉換為 WAV 格式
        audio_data = save_audio_to_wav(recording, sample_rate)
        
        # 使用 speech_recognition 進行識別
        audio_data.seek(0)
        with sr.AudioFile(audio_data) as source:
            audio = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio, language='zh-TW')
                print(f"識別結果: {text}")
            except sr.UnknownValueError:
                print("無法識別語音")
            except sr.RequestError as e:
                print(f"無法連接到Google語音識別服務；{e}")
    
    except Exception as e:
        print(f"發生錯誤: {e}")

if __name__ == "__main__":
    # 安裝需要的套件：
    # pip install sounddevice
    # pip install numpy
    
    print("語音識別測試" \
    "程式")
    print("----------------")
    
    while True:
        test_microphone()
        choice = input("按Enter繼續測試，輸入q退出：")
        if choice.lower() == 'q':
            break
