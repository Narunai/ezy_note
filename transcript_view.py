import os
import shutil
import time
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
    QPushButton, QFrame, QMessageBox, QSplitter, QComboBox,
    QListView, QFileDialog, QApplication
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QGuiApplication
from database import MEDIA_DIR

class TranscriptViewWidget(QWidget):
    transcript_updated = Signal(dict)

    def __init__(self, audio_engine, db, parent=None):
        super().__init__(parent)
        self.audio_engine = audio_engine
        self.db = db
        self.current_note = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # 1. Header Info Banner & Audio Track Selector & Language
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #201D1A;
                border: 1px solid #332E28;
                border-radius: 8px;
                padding: 6px;
            }
        """)
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(8, 4, 8, 4)
        info_layout.setSpacing(8)

        track_sel_label = QLabel("Track:")
        track_sel_label.setStyleSheet("font-weight: bold; font-size: 11px; color: #D4A373;")
        info_layout.addWidget(track_sel_label)

        self.track_select_combo = QComboBox()
        self.track_select_combo.setView(QListView())
        self.track_select_combo.setStyleSheet("min-width: 160px; font-size: 11px;")
        info_layout.addWidget(self.track_select_combo)

        lang_label = QLabel("Language:")
        lang_label.setStyleSheet("font-size: 11px; color: #A89F91;")
        info_layout.addWidget(lang_label)

        self.lang_combo = QComboBox()
        self.lang_combo.setView(QListView())
        self.lang_combo.setStyleSheet("min-width: 110px; font-size: 11px;")
        self.lang_combo.addItem("🇹🇭 Thai (ไทย)", "th-TH")
        self.lang_combo.addItem("🇺🇸 English (US)", "en-US")
        info_layout.addWidget(self.lang_combo)

        self.import_audio_btn = QPushButton("📂 + Import Audio")
        self.import_audio_btn.setObjectName("SecondaryButton")
        self.import_audio_btn.setToolTip("Import audio file from computer (.mp3, .wav, .m4a, .flac, .ogg)")
        self.import_audio_btn.setStyleSheet("font-size: 11px; padding: 3px 8px;")
        self.import_audio_btn.clicked.connect(self.import_audio_file)
        info_layout.addWidget(self.import_audio_btn)

        info_layout.addStretch()

        self.retranscribe_btn = QPushButton("🔄 Retranscribe (ถอดเสียงใหม่)")
        self.retranscribe_btn.setCursor(Qt.PointingHandCursor)
        self.retranscribe_btn.setStyleSheet("""
            QPushButton {
                background-color: #8B5E3C;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 11px;
                padding: 4px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #A27046;
            }
        """)
        self.retranscribe_btn.setToolTip("Click to transcribe audio again with the selected language")
        self.retranscribe_btn.clicked.connect(self.retranscribe_audio)
        info_layout.addWidget(self.retranscribe_btn)

        layout.addWidget(info_frame)

        # 2. Splitter for Transcript vs AI Summary
        splitter = QSplitter(Qt.Vertical)

        # Transcript box
        transcript_container = QWidget()
        tr_layout = QVBoxLayout(transcript_container)
        tr_layout.setContentsMargins(0, 0, 0, 0)
        tr_layout.setSpacing(4)

        tr_header = QHBoxLayout()
        tr_label = QLabel("Detailed Audio Transcript Lines:")
        tr_label.setStyleSheet("font-weight: bold; color: #F5EFE6; font-size: 12px;")
        tr_header.addWidget(tr_label)
        tr_header.addStretch()

        copy_tr_btn = QPushButton("Copy Transcript")
        copy_tr_btn.setObjectName("SecondaryButton")
        copy_tr_btn.setStyleSheet("font-size: 11px; padding: 2px 8px;")
        copy_tr_btn.clicked.connect(self.copy_transcript)
        tr_header.addWidget(copy_tr_btn)

        tr_layout.addLayout(tr_header)

        self.transcript_edit = QTextEdit()
        self.transcript_edit.setObjectName("TranscriptTextEdit")
        self.transcript_edit.setPlaceholderText("No transcript available. Record voice clips or import audio files to generate speech-to-text transcript...")
        tr_layout.addWidget(self.transcript_edit)
        splitter.addWidget(transcript_container)

        # AI Summary box
        summary_container = QWidget()
        sum_layout = QVBoxLayout(summary_container)
        sum_layout.setContentsMargins(0, 0, 0, 0)
        sum_layout.setSpacing(4)

        sum_header = QHBoxLayout()
        sum_label = QLabel("AI Meeting Summary & Action Items:")
        sum_label.setStyleSheet("font-weight: bold; color: #D4A373; font-size: 12px;")
        sum_header.addWidget(sum_label)
        sum_header.addStretch()

        self.summarize_btn = QPushButton("🤖 สรุปเนื้อหาเสียง (Summarize with AI)")
        self.summarize_btn.setCursor(Qt.PointingHandCursor)
        self.summarize_btn.setStyleSheet("""
            QPushButton {
                background-color: #D97706;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 11px;
                padding: 3px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #F59E0B;
            }
        """)
        self.summarize_btn.setToolTip("Click to analyze transcript and summarize core topic & action items")
        self.summarize_btn.clicked.connect(self.generate_ai_summary)
        sum_header.addWidget(self.summarize_btn)

        copy_sum_btn = QPushButton("Copy Summary")
        copy_sum_btn.setObjectName("SecondaryButton")
        copy_sum_btn.setStyleSheet("font-size: 11px; padding: 2px 8px;")
        copy_sum_btn.clicked.connect(self.copy_summary)
        sum_header.addWidget(copy_sum_btn)

        sum_layout.addLayout(sum_header)

        self.summary_edit = QTextEdit()
        self.summary_edit.setObjectName("TranscriptTextEdit")
        self.summary_edit.setPlaceholderText("No AI summary available yet. Click '🤖 สรุปเนื้อหาเสียง (Summarize with AI)' to generate meeting summary...")
        sum_layout.addWidget(self.summary_edit)
        splitter.addWidget(summary_container)

        layout.addWidget(splitter, 1)

    def load_note(self, note):
        self.current_note = note
        self.populate_track_selector()
        if note:
            self.transcript_edit.setText(note.get("transcript", ""))
            self.summary_edit.setText(note.get("summary", ""))
        else:
            self.transcript_edit.clear()
            self.summary_edit.clear()

    def populate_track_selector(self):
        self.track_select_combo.blockSignals(True)
        self.track_select_combo.clear()
        if not self.current_note:
            self.track_select_combo.addItem("All Tracks (ถอดเสียงทุกไฟล์)")
            self.track_select_combo.blockSignals(False)
            return

        audio_files = self.current_note.get("audio_files", [])
        legacy_path = self.current_note.get("audio_path", "")

        self.track_select_combo.addItem("All Tracks (ถอดเสียงทุกไฟล์)")

        if audio_files:
            for idx, item in enumerate(audio_files):
                dur = item.get("duration", 0) if isinstance(item, dict) else 0
                name = item.get("name", f"Voice #{idx+1}") if isinstance(item, dict) else f"Voice #{idx+1}"
                self.track_select_combo.addItem(f"🎵 {name} ({dur}s)")
        elif legacy_path:
            self.track_select_combo.addItem("🎵 Voice #1 (Legacy)")

        self.track_select_combo.blockSignals(False)

    def get_updated_data(self):
        if self.current_note:
            self.current_note["transcript"] = self.transcript_edit.toPlainText()
            self.current_note["summary"] = self.summary_edit.toPlainText()
        return self.current_note

    def generate_ai_summary(self):
        transcript_text = self.transcript_edit.toPlainText().strip()
        if not transcript_text:
            QMessageBox.information(self, "Notice", "ไม่พบข้อความถอดเสียงสำหรับสรุป\nกรุณาบันทึกเสียงหรือถอดเสียงก่อนกดสรุปครับ")
            return

        self.summarize_btn.setEnabled(False)
        self.summarize_btn.setText("⏳ กำลังวิเคราะห์และสรุปประเด็น...")
        QApplication.processEvents()

        try:
            summary = self.audio_engine.generate_summary(transcript_text)
            self.summary_edit.setText(summary)
            if self.current_note:
                self.current_note["summary"] = summary
                self.current_note["transcript"] = transcript_text
                self.db.add_or_update_note(self.current_note)
                self.transcript_updated.emit(self.current_note)

            QMessageBox.information(self, "สำเร็จ", "สรุปประเด็นสำคัญของเนื้อหาเสียงเรียบร้อยแล้ว!")
        except Exception as e:
            QMessageBox.critical(self, "ข้อผิดพลาด", f"เกิดข้อผิดพลาดในการสรุป:\n{str(e)}")
        finally:
            self.summarize_btn.setEnabled(True)
            self.summarize_btn.setText("🤖 สรุปเนื้อหาเสียง (Summarize with AI)")

    def import_audio_file(self):
        if not self.current_note:
            QMessageBox.warning(self, "Warning", "Please select or create a note first.")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Audio File", "", "Audio Files (*.wav *.mp3 *.m4a *.aac *.flac *.ogg *.wma)"
        )
        if not file_path:
            return

        os.makedirs(MEDIA_DIR, exist_ok=True)
        ext = os.path.splitext(file_path)[1]
        dest_filename = f"audio_{int(time.time() * 1000)}{ext}"
        dest_path = os.path.join(MEDIA_DIR, dest_filename)
        shutil.copy2(file_path, dest_path)

        duration = self.audio_engine.get_audio_duration(dest_path)
        audio_files = self.current_note.setdefault("audio_files", [])
        base_title = os.path.splitext(os.path.basename(file_path))[0]
        track_name = f"{base_title[:18]}" if base_title else f"Audio #{len(audio_files)+1}"

        new_clip = {
            "path": dest_path,
            "duration": duration,
            "name": track_name
        }
        audio_files.append(new_clip)

        lang = self.lang_combo.currentData() or "th-TH"
        transcript = self.audio_engine.transcribe_audio(dest_path, language=lang)
        summary = self.audio_engine.generate_summary(transcript)
        existing_tr = self.current_note.get("transcript", "")
        self.current_note["transcript"] = (existing_tr + "\n\n" + f"[{track_name}]\n" + transcript).strip()
        self.current_note["summary"] = summary

        self.load_note(self.current_note)
        self.db.add_or_update_note(self.current_note)
        self.transcript_updated.emit(self.current_note)

    def retranscribe_audio(self):
        if not self.current_note:
            QMessageBox.warning(self, "Warning", "Please select or create a note first.")
            return

        audio_files = self.current_note.get("audio_files", [])
        legacy_path = self.current_note.get("audio_path", "")

        audio_paths = []
        if audio_files:
            for idx, item in enumerate(audio_files):
                if isinstance(item, dict) and item.get("path"):
                    audio_paths.append((item.get("name", f"Voice #{idx+1}"), item["path"]))
                elif isinstance(item, str):
                    audio_paths.append((f"Voice #{idx+1}", item))
        elif legacy_path:
            audio_paths.append(("Voice #1 (Legacy)", legacy_path))

        if not audio_paths:
            QMessageBox.information(self, "Notice", "ไม่พบไฟล์เสียงในโน้ตนี้\nกรุณาบันทึกเสียงหรือนำเข้าไฟล์เสียงก่อนครับ")
            return

        selected_idx = self.track_select_combo.currentIndex()
        target_paths = []

        if selected_idx <= 0 or selected_idx > len(audio_paths):
            # Transcribe All
            target_paths = audio_paths
        else:
            # Transcribe specific selected track
            target_paths = [audio_paths[selected_idx - 1]]

        lang = self.lang_combo.currentData() or "th-TH"

        # Visual feedback during transcription
        self.retranscribe_btn.setEnabled(False)
        self.retranscribe_btn.setText("⏳ กำลังถอดเสียง...")
        QApplication.processEvents()

        try:
            all_transcripts = []
            for name, path in target_paths:
                if os.path.exists(path):
                    t = self.audio_engine.transcribe_audio(path, language=lang)
                    all_transcripts.append(f"[{name}]\n{t}")
                else:
                    all_transcripts.append(f"[{name}]\n(ไม่พบไฟล์เสียง: {os.path.basename(path)})")

            new_transcript_block = "\n\n".join(all_transcripts)

            if len(target_paths) == 1 and len(audio_paths) > 1:
                existing_transcript = self.current_note.get("transcript", "")
                target_header = f"[{target_paths[0][0]}]"
                if target_header in existing_transcript:
                    # Replace existing track section cleanly
                    pattern = rf"\[{re.escape(target_paths[0][0])}\][\s\S]*?(?=\n\n\[|\Z)"
                    transcript_text = re.sub(pattern, new_transcript_block, existing_transcript).strip()
                else:
                    transcript_text = (existing_transcript + "\n\n" + new_transcript_block).strip()
            else:
                transcript_text = new_transcript_block

            summary_text = self.audio_engine.generate_summary(transcript_text)

            self.transcript_edit.setText(transcript_text)
            self.summary_edit.setText(summary_text)

            self.current_note["transcript"] = transcript_text
            self.current_note["summary"] = summary_text
            self.db.add_or_update_note(self.current_note)
            self.transcript_updated.emit(self.current_note)

            QMessageBox.information(self, "สำเร็จ", f"ถอดเสียง ({lang}) สำหรับ {len(target_paths)} ไฟล์สำเร็จเรียบร้อยแล้ว!")
        except Exception as e:
            QMessageBox.critical(self, "ข้อผิดพลาด", f"เกิดข้อผิดพลาดในการถอดเสียง:\n{str(e)}")
        finally:
            self.retranscribe_btn.setEnabled(True)
            self.retranscribe_btn.setText("🔄 Retranscribe (ถอดเสียงใหม่)")

    def copy_transcript(self):
        text = self.transcript_edit.toPlainText()
        if text:
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(text)
            QMessageBox.information(self, "Success", "คัดลอกข้อความถอดเสียงไปยังคลิปบอร์ดแล้ว")

    def copy_summary(self):
        text = self.summary_edit.toPlainText()
        if text:
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(text)
            QMessageBox.information(self, "Success", "คัดลอกสรุป AI ไปยังคลิปบอร์ดแล้ว")
