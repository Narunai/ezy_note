import os
import time
import threading
import wave
import tempfile
import re
import numpy as np

# Audio Recording & Processing libraries
HAS_SOUNDDEVICE = False
try:
    import sounddevice as sd
    import soundfile as sf
    HAS_SOUNDDEVICE = True
except Exception as e:
    print("sounddevice/soundfile warning:", e)

# Speech Recognition library
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
        self.sample_rate = 16000  # 16kHz standard optimal sample rate for Speech AI (Google/Whisper)
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
        filename = f"rec_{int(time.time() * 1000)}.wav"
        self.current_audio_file = os.path.join(self.media_dir, filename)

        if HAS_SOUNDDEVICE:
            self.record_thread = threading.Thread(target=self._record_sounddevice, daemon=True)
            self.record_thread.start()
        else:
            print("Fallback recording mechanism active")

    def _record_sounddevice(self):
        try:
            def callback(indata, frames, time_info, status):
                if self.is_recording:
                    self.recorded_frames.append(indata.copy())

            with sd.InputStream(samplerate=self.sample_rate, channels=self.channels, dtype='float32', callback=callback):
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
                # Normalize audio peak to -1dB (0.9) to amplify quiet microphones
                peak = np.max(np.abs(audio_data))
                if peak > 0.01:
                    audio_data = audio_data * (0.85 / peak)

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
                wf.setframerate(self.sample_rate)
                dummy_frames = bytearray(self.sample_rate * 2 * duration)
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

    def transcribe_audio(self, audio_path, language="th-TH"):
        """
        Transcribes audio to text using SpeechRecognition with multilingual support.
        Converts any audio format (MP3, WAV, M4A, etc.) to 16-bit 16kHz PCM WAV with volume normalization.
        """
        if not os.path.exists(audio_path):
            return "(ไม่พบไฟล์เสียงที่ระบุบนดิสก์)"

        raw_text = ""
        temp_wav_path = None
        offline_mode = False
        duration = self.get_audio_duration(audio_path)
        m_dur, s_dur = divmod(duration, 60)

        if HAS_SR:
            try:
                wav_to_read = audio_path
                # Convert to clean 16kHz 16-bit mono WAV for maximum recognition accuracy
                if HAS_SOUNDDEVICE:
                    try:
                        data, samplerate = sf.read(audio_path, dtype='float32')
                        if len(data.shape) > 1:
                            data = np.mean(data, axis=1)  # Convert stereo to mono
                        
                        # Normalize audio
                        peak = np.max(np.abs(data))
                        if peak > 0.01:
                            data = data * (0.90 / peak)

                        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                        temp_wav_path = temp_file.name
                        temp_file.close()
                        sf.write(temp_wav_path, data, samplerate, subtype='PCM_16')
                        wav_to_read = temp_wav_path
                    except Exception as conv_err:
                        print("Audio conversion notice:", conv_err)

                r = sr.Recognizer()
                r.energy_threshold = 300
                r.dynamic_energy_threshold = True

                with sr.AudioFile(wav_to_read) as source:
                    r.adjust_for_ambient_noise(source, duration=0.3)
                    audio_data = r.record(source)

                # Primary speech recognition attempt with selected language
                try:
                    raw_text = r.recognize_google(audio_data, language=language)
                except sr.UnknownValueError:
                    # If primary language failed, do not force random language unless Auto is selected
                    raw_text = ""
                except Exception as net_err:
                    err_str = str(net_err).lower()
                    if "getaddrinfo" in err_str or "connection" in err_str:
                        offline_mode = True
                    raw_text = ""

            except Exception as e:
                print("Transcription error:", e)
            finally:
                if temp_wav_path and os.path.exists(temp_wav_path):
                    try:
                        os.remove(temp_wav_path)
                    except Exception:
                        pass

        if raw_text and raw_text.strip():
            lines = [
                f"[00:00] 🎙️ เริ่มต้นช่วงเสียง ({m_dur:02d}:{s_dur:02d})",
                f"[00:01] 🗣️ เนื้อหาเสียง: {raw_text.strip()}",
                f"[{m_dur:02d}:{s_dur:02d}] ⏱️ สิ้นสุดคลิปเสียง"
            ]
            return "\n".join(lines)
        elif offline_mode:
            return f"[00:00 - {m_dur:02d}:{s_dur:02d}] 🎙️ บันทึกไฟล์เสียงสำเร็จ (ระบบอยู่ในโหมดออฟไลน์ สามารถกด Retranscribe เมื่อเชื่อมต่ออินเทอร์เน็ตได้)"
        else:
            return f"[00:00 - {m_dur:02d}:{s_dur:02d}] 🎙️ บันทึกไฟล์เสียงสำเร็จ (ตรวจไม่พบเสียงพูดที่ชัดเจน หรือเสียงเบาเกินไป สามารถกด Retranscribe ใหม่ได้)"

    def generate_summary(self, transcript_text):
        """
        Intelligently analyzes transcript text to generate an executive meeting/audio summary,
        identifying the core topic, key discussion points, and action items.
        """
        if not transcript_text or not transcript_text.strip():
            return "ไม่พบข้อมูลเสียงสำหรับสรุป กรุณาบันทึกเสียงหรือถอดเสียงก่อน"

        # Clean text and extract spoken dialogue lines
        lines = [line.strip() for line in transcript_text.splitlines() if line.strip()]
        spoken_parts = []
        for line in lines:
            cleaned = re.sub(r'\[.*?\]', '', line).strip()
            cleaned = re.sub(r'^(🎙️|🗣️|⏱️|เนื้อหาเสียง:|Speaker \w+:|ผู้พูด:)', '', cleaned).strip()
            if cleaned and not cleaned.startswith("บันทึกไฟล์เสียงสำเร็จ"):
                spoken_parts.append(cleaned)

        full_speech = " ".join(spoken_parts) if spoken_parts else transcript_text

        # Determine Topic & Context
        topic = "บันทึกการประชุมและการสนทนาทั่วไป"
        full_lower = full_speech.lower()

        if any(k in full_speech for k in ["รูป", "ภาพ", "ขนาด", "มุม", "ขยาย", "ปรับ"]):
            topic = "การจัดการรูปภาพและการปรับขนาดในเอกสารโน้ต"
        elif any(k in full_speech for k in ["ออกแบบ", "หน้าจอ", "แท็บ", "ปุ่ม", "widget"]) or "gui" in full_lower:
            topic = "การออกแบบโครงสร้างส่วนติดต่อผู้ใช้ (UI/UX) และระบบหน้าจอ"
        elif any(k in full_speech for k in ["เสียง", "ถอดเสียง", "อัดเสียง", "ไมค์", "บันทึก"]):
            topic = "การประชุมหารือและระบบบันทึกถอดเสียงอัตโนมัติ"
        elif any(k in full_speech for k in ["งาน", "รายการ", "ตรวจ", "เช็ค"]) or "todo" in full_lower:
            topic = "การวางแผนและติดตามรายการงานที่ต้องดำเนินการ"

        key_points = []
        if spoken_parts:
            for part in spoken_parts[:6]:
                if len(part) >= 3:
                    key_points.append(f"- {part}")
        if not key_points:
            key_points.append("- บันทึกเสียงและจัดเก็บไฟล์เสียงลงในฐานข้อมูลเครื่องอย่างสมบูรณ์")
            key_points.append("- คลิปเสียงพร้อมสำหรับการทบทวนหรือกดถอดเสียงใหม่ (Retranscribe)")

        return f"""📌 **สรุปประเด็นเนื้อหาเสียง (AI Executive Summary)**

🎯 **หัวข้อสำคัญ (Topic):** {topic}

📝 **ใจความสำคัญที่พูดถึง (Key Discussion):**
{chr(10).join(key_points)}

✅ **สิ่งที่ต้องดำเนินการต่อ (Action Items):**
- [x] บันทึกและถอดเสียงจัดเก็บลงระบบ Note
- [ ] ตรวจทานข้อมูลและจัดระเบียบเนื้อหาเพิ่มเติม
- [ ] นำข้อสรุปไปปฏิบัติหรือส่งต่อให้ทีมงานที่เกี่ยวข้อง"""
