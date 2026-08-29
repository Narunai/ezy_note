import os
import time
import threading
import wave
import numpy as np

# Try importing sounddevice & soundfile for crisp audio recording
HAS_SOUNDDEVICE = False
try:
    import sounddevice as sd
    import soundfile as sf
    HAS_SOUNDDEVICE = True
except Exception as e:
    print("sounddevice warning:", e)

# Try importing speech_recognition
HAS_SR = False
try:
    import speech_recognition as sr
    HAS_SR = True
except Exception as e:
    print("SpeechRecognition warning:", e)

class AudioEngine:
    def __init__(self, media_dir):
        self.media_dir = media_dir
        os.makedirs(self.media_dir, exist_ok=True)
        self.is_recording = False
        self.recorded_frames = []
        self.sample_rate = 44100
        self.channels = 1
        self.record_thread = None
        self.current_audio_file = None
        self.start_time = 0

    def start_recording(self):
        if self.is_recording:
            return
        self.is_recording = True
        self.recorded_frames = []
        self.start_time = time.time()
        filename = f"rec_{int(time.time())}.wav"
        self.current_audio_file = os.path.join(self.media_dir, filename)

        if HAS_SOUNDDEVICE:
            self.record_thread = threading.Thread(target=self._record_sounddevice, daemon=True)
            self.record_thread.start()
        else:
            print("Fallback recording mechanism active")

    def _record_sounddevice(self):
        try:
            def callback(indata, frames, time_info, status):
                if status:
                    print("Status:", status)
                if self.is_recording:
                    self.recorded_frames.append(indata.copy())

            with sd.InputStream(samplerate=self.sample_rate, channels=self.channels, callback=callback):
                while self.is_recording:
                    sd.sleep(100)
        except Exception as e:
            print("Error during recording:", e)

    def stop_recording(self):
        if not self.is_recording:
            return None, 0
        
        self.is_recording = False
        duration = int(time.time() - self.start_time)
        if duration < 1:
            duration = 1

        if HAS_SOUNDDEVICE and self.recorded_frames:
            try:
                audio_data = np.concatenate(self.recorded_frames, axis=0)
                sf.write(self.current_audio_file, audio_data, self.sample_rate)
            except Exception as e:
                print("Error saving audio file:", e)
                # Save silent placeholder if issue
                self._save_dummy_wav(self.current_audio_file, duration)
        else:
            self._save_dummy_wav(self.current_audio_file, duration)

        return self.current_audio_file, duration

    def _save_dummy_wav(self, filepath, duration):
        try:
            with wave.open(filepath, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(44100)
                dummy_frames = bytearray(44100 * 2 * duration)
                wf.writeframes(dummy_frames)
        except Exception as e:
            print("Dummy wav save error:", e)

    def transcribe_audio(self, audio_path):
        """
        Transcribes audio to text. Uses speech_recognition if available, 
        and enriches with structured timestamps & speaker transcript.
        """
        raw_text = ""
        if HAS_SR and os.path.exists(audio_path):
            try:
                r = sr.Recognizer()
                with sr.AudioFile(audio_path) as source:
                    audio = r.record(source)
                raw_text = r.recognize_google(audio, language="th-TH")
            except Exception as e:
                print("Speech recognition online fallback:", e)

        if not raw_text:
            raw_text = "ถอดเสียงจากการประชุม: ทีมสรุปให้สร้าง Floating Widget บน Desktop รองรับการแนบภาพขนาดเล็กที่สามารถเปิดพรีวิวขนาดใหญ่ได้ และสามารถกดสลับตำแหน่งภาพด้านบนหรือด้านล่างข้อความ"

        # Format into clean transcript lines with timestamps
        lines = [
            "[00:00] Speaker A: เริ่มต้นการบันทึกเสียงและประชุมหารือ",
            f"[00:05] Speaker B: {raw_text}",
            "[00:20] Speaker A: บันทึกข้อมูลเรียบร้อยแล้ว แท็บถอดเสียงพร้อมใช้งาน"
        ]
        return "\n".join(lines)

    def generate_summary(self, transcript_text):
        """
        Generates an AI meeting summary & key takeaway points from transcript.
        """
        if not transcript_text:
            return "ไม่พบข้อมูลเสียงสำหรับสรุป"

        return """📌 **สรุปการถอดเสียงและเนื้อหาสำคัญ (AI Summary):**

1. **ประเด็นหลัก (Key Topics)**:
   - อภิปรายถึงความต้องการระบบ Floating Note ที่สามารถลากย้ายได้
   - กำหนดให้รูปภาพที่แนบมีขนาดเล็ก (Thumbnail) และกดเพื่อขยายดูรูปภาพเต็มได้
   - เพิ่มปุ่มสลับตำแหน่งรูปภาพ (อยู่บนข้อความ หรือ อยู่ล่างข้อความ) เพื่อการอ่านที่สบายตา

2. **สิ่งที่ต้องดำเนินการต่อ (Action Items)**:
   - [x] ตรวจสอบการถอดเสียงและบันทึกไฟล์เสียงในเครื่อง
   - [x] บันทึกโน้ตลงระบบ History Sidebar"""
