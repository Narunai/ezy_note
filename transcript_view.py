import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
    QPushButton, QFrame, QMessageBox, QSplitter, QComboBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QGuiApplication

class TranscriptViewWidget(QWidget):
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
        self.track_select_combo.setStyleSheet("""
            QComboBox {
                background-color: #161412;
                border: 1px solid #332E28;
                border-radius: 4px;
                padding: 2px 6px;
                color: #F5EFE6;
                font-size: 11px;
                min-width: 150px;
            }
        """)
        info_layout.addWidget(self.track_select_combo)
        info_layout.addStretch()

        self.retranscribe_btn = QPushButton("Retranscribe Selected Track")
        self.retranscribe_btn.setObjectName("SecondaryButton")
        self.retranscribe_btn.setCursor(Qt.PointingHandCursor)
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
        self.transcript_edit.setPlaceholderText("No transcript available. Record voice clips to generate transcript lines...")
        tr_layout.addWidget(self.transcript_edit)
        splitter.addWidget(transcript_container)

        # 2. AI Summary box (High-Contrast Text)
        summary_container = QWidget()
        sum_layout = QVBoxLayout(summary_container)
        sum_layout.setContentsMargins(0, 0, 0, 0)
        sum_layout.setSpacing(6)

        sum_label = QLabel("AI Meeting Summary & Action Items:")
        sum_label.setStyleSheet("font-weight: bold; color: #D4A373; font-size: 12px;")
        sum_layout.addWidget(sum_label)

        self.summary_edit = QTextEdit()
        self.summary_edit.setObjectName("TranscriptTextEdit")
        self.summary_edit.setPlaceholderText("AI generated summary and action items will appear here...")
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

    def populate_track_selector(self):
        self.track_select_combo.clear()
        if not self.current_note:
            self.track_select_combo.addItem("All Tracks")
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

    def get_updated_data(self):
        if self.current_note:
            self.current_note["transcript"] = self.transcript_edit.toPlainText()
            self.current_note["summary"] = self.summary_edit.toPlainText()
        return self.current_note

    def retranscribe_audio(self):
        if not self.current_note:
            return

        audio_files = self.current_note.get("audio_files", [])
        legacy_path = self.current_note.get("audio_path", "")

        audio_paths = []
        if audio_files:
            for item in audio_files:
                if isinstance(item, dict) and item.get("path"):
                    audio_paths.append((item.get("name", "Voice Clip"), item["path"]))
                elif isinstance(item, str):
                    audio_paths.append(("Voice Clip", item))
        elif legacy_path:
            audio_paths.append(("Legacy Voice Clip", legacy_path))

        if not audio_paths:
            QMessageBox.information(self, "Notice", "No recorded audio clips found in this note. Record audio first.")
            return

        selected_idx = self.track_select_combo.currentIndex()
        target_paths = []

        if selected_idx <= 0 or selected_idx > len(audio_paths):
            # Transcribe All
            target_paths = audio_paths
        else:
            # Transcribe specific selected track
            target_paths = [audio_paths[selected_idx - 1]]

        all_transcripts = []
        for name, path in target_paths:
            if os.path.exists(path):
                t = self.audio_engine.transcribe_audio(path)
                all_transcripts.append(f"[{name}]\n{t}")

        transcript_text = "\n\n".join(all_transcripts)
        summary_text = self.audio_engine.generate_summary(transcript_text)

        self.transcript_edit.setText(transcript_text)
        self.summary_edit.setText(summary_text)

        self.current_note["transcript"] = transcript_text
        self.current_note["summary"] = summary_text
        self.db.add_or_update_note(self.current_note)

        QMessageBox.information(self, "Success", f"Transcribed {len(target_paths)} audio track(s) successfully!")

    def copy_transcript(self):
        text = self.transcript_edit.toPlainText()
        if text:
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(text)
            QMessageBox.information(self, "Success", "Copied transcript to Clipboard.")
