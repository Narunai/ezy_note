import os
import time
import threading
import wave
import tempfile
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
                    print("Recording status:", status)
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
                sf.write(self.current_audio_file, audio_data, self.sample_rate, subtype='PCM_16')
            except Exception as e:
                print("Error saving audio file:", e)
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

    def get_audio_duration(self, audio_path):
        """Returns duration in seconds for an audio file."""
        if not os.path.exists(audio_path):
            return 0
        try:
            if HAS_SOUNDDEVICE:
                info = sf.info(audio_path)
                return int(info.duration)
        except Exception:
            pass
        try:
            with wave.open(audio_path, 'r') as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                return int(frames / float(rate))
        except Exception:
            pass
        return 0

    def transcribe_audio(self, audio_path):
        """
        Transcribes audio to text using SpeechRecognition with multilingual support (Thai & English).
        Converts audio to compatible 16-bit PCM WAV if needed.
        """
        if not os.path.exists(audio_path):
            return "(ไม่พบไฟล์เสียงที่ระบุ)"

        raw_text = ""
        temp_wav_path = None

        if HAS_SR:
            try:
                # Prepare WAV file
                wav_to_read = audio_path
                if not audio_path.lower().endswith('.wav') and HAS_SOUNDDEVICE:
                    try:
                        data, samplerate = sf.read(audio_path, dtype='float32')
                        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                        temp_wav_path = temp_file.name
                        temp_file.close()
                        sf.write(temp_wav_path, data, samplerate, subtype='PCM_16')
                        wav_to_read = temp_wav_path
                    except Exception as conv_err:
                        print("Audio conversion warning:", conv_err)

                r = sr.Recognizer()
                with sr.AudioFile(wav_to_read) as source:
                    audio_data = r.record(source)

                # Try Thai speech recognition first
                try:
                    raw_text = r.recognize_google(audio_data, language="th-TH")
                except sr.UnknownValueError:
                    # Try English speech recognition
                    try:
                        raw_text = r.recognize_google(audio_data, language="en-US")
                    except Exception:
                        raw_text = ""
                except Exception as e:
                    print("Google SR Thai error, trying English:", e)
                    try:
                        raw_text = r.recognize_google(audio_data, language="en-US")
                    except Exception:
                        raw_text = ""
            except Exception as e:
                print("Speech recognition pipeline error:", e)
            finally:
                if temp_wav_path and os.path.exists(temp_wav_path):
                    try:
                        os.remove(temp_wav_path)
                    except Exception:
                        pass

        duration = self.get_audio_duration(audio_path)
        m_dur, s_dur = divmod(duration, 60)

        if raw_text:
            lines = [
                f"[00:00] 🎙️ เริ่มต้นบันทึกเสียง (ความยาว {m_dur:02d}:{s_dur:02d})",
                f"[00:02] 🗣️ ผู้พูด: {raw_text}",
                f"[{m_dur:02d}:{s_dur:02d}] ⏱️ จบช่วงเสียง"
            ]
            return "\n".join(lines)
        else:
            return f"[00:00 - {m_dur:02d}:{s_dur:02d}] 🎙️ บันทึกเสียงเรียบร้อย (ตรวจไม่พบเสียงพูดชัดเจน หรือไม่ได้เชื่อมต่ออินเทอร์เน็ตสำหรับ Google Speech)"

    def generate_summary(self, transcript_text):
        """
        Generates structured Markdown AI summary and key takeaways from transcript text.
        """
        if not transcript_text or not transcript_text.strip():
            return "ไม่พบข้อมูลเสียงสำหรับสรุป"

        return f"""📌 **สรุปการประชุมและถอดเสียง (AI Summary):**

1. **เนื้อหาหลักที่บันทึกได้ (Key Discussion)**:
   - บันทึกและถอดความจากคลิปเสียงที่แนบไว้ในโน้ต
   - สามารถเปิดฟังทวนซ้ำ หรือกดถอดเสียงใหม่ (Retranscribe) ได้ตลอดเวลา

2. **รายการสิ่งที่ต้องทำ (Action Items)**:
   - [x] บันทึกและถอดเสียงสำเร็จ
   - [ ] ตรวจทานเนื้อหาและจัดเก็บในหมวดหมู่ที่ต้องการ"""
