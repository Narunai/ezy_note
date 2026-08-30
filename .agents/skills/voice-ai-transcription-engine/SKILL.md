---
name: voice-ai-transcription-engine
description: Architecture, verification procedures, and best practices for NoteGod Voice AI transcription, audio processing, and PySide6 Win32 DWM Snap integration.
---

# Voice AI Transcription & Audio Engine Architecture (NoteGod)

This skill documents the complete design patterns, audio processing pipeline, speech recognition engines, and verification checklists for the NoteGod Desktop Application.

---

## 1. Core Audio Pipeline

### A. Recording Architecture
- **Engine**: `sounddevice` with float32 streaming input stream (`sd.InputStream`).
- **Optimal Sample Rate**: `16000 Hz` (16kHz), 1 channel (Mono).
  - *Why 16kHz Mono?*: Standard speech recognition models (Google Speech Recognition, OpenAI Whisper, Vosk, Sphinx) are trained on 16kHz mono audio. Recording directly in 16kHz mono minimizes CPU overhead and eliminates resampling artifacts.
- **Dynamic Normalization**:
  ```python
  peak = np.max(np.abs(audio_data))
  if peak > 0.01:
      audio_data = audio_data * (0.85 / peak) # Normalize peak to -1dB
  ```
  Ensures quiet microphone input is amplified cleanly without clipping.

### B. Transcription & Multilingual Processing
- **Engine**: `speech_recognition` (`sr.Recognizer`).
- **Language Codes**:
  - `th-TH`: Thai Speech Recognition (Google Cloud / Web Speech API backend).
  - `en-US`: US English Speech Recognition.
- **Ambient Noise Adjustment**:
  ```python
  r.adjust_for_ambient_noise(source, duration=0.3)
  ```
- **Error Handling & Fallback**:
  - Catch `sr.UnknownValueError` gracefully without forcing unmatched foreign language guesses.
  - Detect network / offline states (`getaddrinfo`, connection timeout) and present informative UI notices.

### C. AI Meeting Summary & Action Item Extraction
- **Rule-based & Contextual Keyword Extraction**:
  - Analyzes spoken sentences, extracts topics (UI/UX, Meeting, Image management, Tasks).
  - Structures output into:
    1. 🎯 **หัวข้อสำคัญ (Topic)**
    2. 📝 **ใจความสำคัญที่พูดถึง (Key Discussion Points)**
    3. ✅ **สิ่งที่ต้องดำเนินการต่อ (Action Items)**

---

## 2. Windows Native Aero Snap & Frameless Window Integration

To achieve 100% native Windows Snap (docking to left/right half screen, Win + Left/Right, hardware-accelerated border resizing):
1. **Window Flags**:
   - `WS_THICKFRAME | WS_MAXIMIZEBOX | WS_MINIMIZEBOX | WS_SYSMENU | WS_CAPTION` (`0x00CF0000`)
2. **Win32 Messages**:
   - `WM_NCCALCSIZE` (`0x0083`): Return `0` to remove OS titlebar border while keeping DWM snap and shadow.
   - `WM_NCHITTEST` (`0x0084`):
     - Return `HTCAPTION` (2) for CustomTitleBar.
     - Return `HTCLIENT` (1) for interactive buttons.
     - Return `HTLEFT`, `HTRIGHT`, `HTTOP`, `HTBOTTOM`, etc. for borders.

---

## 3. Systematic Verification Checklist for Agents

When verifying or enhancing audio / transcription in NoteGod:
1. **Compilation Check**:
   ```bash
   python -m py_compile main.py note_editor.py audio_engine.py transcript_view.py audio_player_widget.py
   ```
2. **Audio File Integrity**:
   - Ensure media files are saved in `~/.notegod/media/` with valid WAV/PCM headers.
3. **Speech Recognition Test**:
   - Run a test transcription on a sample audio file with `language="th-TH"` and `language="en-US"`.
4. **Git Sync**:
   - Commit changes with descriptive commit messages and push to `origin/main`.
