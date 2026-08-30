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
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Header Info Banner & Audio Track Selector
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #201D1A;
                border: 1px solid #332E28;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(8, 4, 8, 4)
        info_layout.setSpacing(8)

        header_text = QLabel("Audio Transcript & AI Summary")
        header_text.setStyleSheet("font-weight: bold; font-size: 13px; color: #D4A373;")
        info_layout.addWidget(header_text)

        track_sel_label = QLabel("Select Audio Track:")
        track_sel_label.setStyleSheet("font-size: 11px; color: #A89F91;")
        info_layout.addWidget(track_sel_label)

        self.track_select_combo = QComboBox()
        self.track_select_combo.setView(QListView())
        self.track_select_combo.setStyleSheet("min-width: 170px;")
        info_layout.addWidget(self.track_select_combo)

        self.import_audio_btn = QPushButton("+ Import Audio")
        self.import_audio_btn.setObjectName("SecondaryButton")
        self.import_audio_btn.setToolTip("Import audio file from computer")
        self.import_audio_btn.setStyleSheet("font-size: 11px; padding: 3px 8px;")
        self.import_audio_btn.clicked.connect(self.import_audio_file)
        info_layout.addWidget(self.import_audio_btn)

        info_layout.addStretch()

        self.retranscribe_btn = QPushButton("Retranscribe Selected Track")
        self.retranscribe_btn.setCursor(Qt.PointingHandCursor)
        self.retranscribe_btn.setStyleSheet("background-color: #8B5E3C; font-weight: bold; font-size: 11px; padding: 4px 12px;")
        self.retranscribe_btn.clicked.connect(self.retranscribe_audio)
        info_layout.addWidget(self.retranscribe_btn)

        layout.addWidget(info_frame)

        # Splitter for Transcript vs AI Summary
        splitter = QSplitter(Qt.Vertical)

        # 1. Transcript box (High-Contrast Text)
        transcript_container = QWidget()
        tr_layout = QVBoxLayout(transcript_container)
        tr_layout.setContentsMargins(0, 0, 0, 0)
        tr_layout.setSpacing(6)

        tr_header = QHBoxLayout()
        tr_label = QLabel("Detailed Audio Transcript Lines:")
        tr_label.setStyleSheet("font-weight: bold; color: #F5EFE6; font-size: 12px;")
        tr_header.addWidget(tr_label)
        tr_header.addStretch()

        copy_tr_btn = QPushButton("Copy Transcript")
        copy_tr_btn.setObjectName("SecondaryButton")
        copy_tr_btn.clicked.connect(self.copy_transcript)
        tr_header.addWidget(copy_tr_btn)

        tr_layout.addLayout(tr_header)

        self.transcript_edit = QTextEdit()
        self.transcript_edit.setObjectName("TranscriptTextEdit")
        self.transcript_edit.setPlaceholderText("No transcript available. Record voice clips or import audio files to generate transcript lines...")
        tr_layout.addWidget(self.transcript_edit)
        splitter.addWidget(transcript_container)

        # 2. AI Summary box (High-Contrast Text) with Dedicated Summarize Button
        summary_container = QWidget()
        sum_layout = QVBoxLayout(summary_container)
        sum_layout.setContentsMargins(0, 0, 0, 0)
        sum_layout.setSpacing(6)

        sum_header = QHBoxLayout()
        sum_label = QLabel("AI Meeting Summary & Action Items:")
        sum_label.setStyleSheet("font-weight: bold; color: #D4A373; font-size: 12px;")
        sum_header.addWidget(sum_label)
        sum_header.addStretch()

        self.summarize_btn = QPushButton("🤖 สรุปเนื้อหาเสียง (Summarize with AI)")
        self.summarize_btn.setCursor(Qt.PointingHandCursor)
        self.summarize_btn.setStyleSheet("background-color: #D97706; color: #FFFFFF; font-weight: bold; font-size: 11px; padding: 4px 12px;")
        self.summarize_btn.setToolTip("กดเพื่อวิเคราะห์และสรุปประเด็นสำคัญว่าเสียงนี้เกี่ยวกับอะไร")
        self.summarize_btn.clicked.connect(self.generate_ai_summary)
        sum_header.addWidget(self.summarize_btn)

        copy_sum_btn = QPushButton("Copy Summary")
        copy_sum_btn.setObjectName("SecondaryButton")
        copy_sum_btn.clicked.connect(self.copy_summary)
        sum_header.addWidget(copy_sum_btn)

        sum_layout.addLayout(sum_header)

        self.summary_edit = QTextEdit()
        self.summary_edit.setObjectName("TranscriptTextEdit")
        self.summary_edit.setPlaceholderText("AI generated summary and action items will appear here... Click '🤖 สรุปเนื้อหาเสียง' to summarize anytime!")
        sum_layout.addWidget(self.summary_edit)
        splitter.addWidget(summary_container)

        splitter.setSizes([280, 220])
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
                self.track_select_combo.addItem(f"{name} ({dur}s)")
        elif legacy_path:
            self.track_select_combo.addItem("Voice #1 (Legacy)")

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

        # Transcribe & Summarize
        transcript = self.audio_engine.transcribe_audio(dest_path)
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
            QMessageBox.information(self, "Notice", "No recorded or imported audio tracks found in this note.\nPlease record or import audio first.")
            return

        selected_idx = self.track_select_combo.currentIndex()
        target_paths = []

        if selected_idx <= 0 or selected_idx > len(audio_paths):
            # Transcribe All
            target_paths = audio_paths
        else:
            # Transcribe specific selected track
            target_paths = [audio_paths[selected_idx - 1]]

        # Visual feedback during transcription
        self.retranscribe_btn.setEnabled(False)
        self.retranscribe_btn.setText("⏳ กำลังถอดเสียง...")
        QApplication.processEvents()

        try:
            all_transcripts = []
            for name, path in target_paths:
                if os.path.exists(path):
                    t = self.audio_engine.transcribe_audio(path)
                    all_transcripts.append(f"[{name}]\n{t}")
                else:
                    all_transcripts.append(f"[{name}]\n(File not found: {os.path.basename(path)})")

            new_transcript_block = "\n\n".join(all_transcripts)

            if len(target_paths) == 1 and len(audio_paths) > 1:
                existing_transcript = self.current_note.get("transcript", "")
                target_header = f"[{target_paths[0][0]}]"
                if target_header in existing_transcript:
                    transcript_text = new_transcript_block
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

            QMessageBox.information(self, "Success", f"ถอดเสียง {len(target_paths)} ไฟล์สำเร็จเรียบร้อยแล้ว!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"เกิดข้อผิดพลาดในการถอดเสียง:\n{str(e)}")
        finally:
            self.retranscribe_btn.setEnabled(True)
            self.retranscribe_btn.setText("Retranscribe Selected Track")

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
