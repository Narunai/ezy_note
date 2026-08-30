import os
import time
import shutil
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, 
    QComboBox, QSlider, QListView, QMessageBox, QFrame, QFileDialog,
    QApplication
)
from PySide6.QtCore import Qt, QUrl, Signal, QTimer
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from database import MEDIA_DIR

class VoiceStudioTabWidget(QWidget):
    audio_files_updated = Signal(dict)

    def __init__(self, audio_engine, db, parent=None):
        super().__init__(parent)
        self.audio_engine = audio_engine
        self.db = db
        self.current_note = None
        self.audio_files = []
        self.is_slider_pressed = False

        # Initialize QMediaPlayer & AudioOutput for multi-format playback
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(1.0)

        self.player.positionChanged.connect(self.on_position_changed)
        self.player.durationChanged.connect(self.on_duration_changed)
        self.player.playbackStateChanged.connect(self.on_playback_state_changed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        # 1. Studio Header Banner
        header_card = QFrame()
        header_card.setStyleSheet("""
            QFrame {
                background-color: #201D1A;
                border: 1px solid #332E28;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(10, 6, 10, 6)
        header_layout.setSpacing(10)

        title_lbl = QLabel("🎙️ Voice & Audio Studio")
        title_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #D4A373;")
        header_layout.addWidget(title_lbl)

        header_layout.addStretch()

        self.rec_btn = QPushButton("🎙️ + Record Voice")
        self.rec_btn.setCursor(Qt.PointingHandCursor)
        self.rec_btn.setStyleSheet("""
            QPushButton {
                background-color: #B91C1C;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 12px;
                padding: 6px 14px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #DC2626;
            }
        """)
        self.rec_btn.clicked.connect(self.toggle_recording)
        header_layout.addWidget(self.rec_btn)

        self.import_btn = QPushButton("📂 + Import Audio File")
        self.import_btn.setObjectName("SecondaryButton")
        self.import_btn.setCursor(Qt.PointingHandCursor)
        self.import_btn.setStyleSheet("font-size: 12px; padding: 6px 12px;")
        self.import_btn.setToolTip("Import audio file from computer (.mp3, .wav, .m4a, .flac, .ogg)")
        self.import_btn.clicked.connect(self.import_audio_file)
        header_layout.addWidget(self.import_btn)

        layout.addWidget(header_card)

        # 2. Main Player Deck Card
        deck_card = QFrame()
        deck_card.setStyleSheet("""
            QFrame {
                background-color: #201D1A;
                border: 1px solid #332E28;
                border-radius: 8px;
                padding: 14px;
            }
        """)
        deck_layout = QVBoxLayout(deck_card)
        deck_layout.setContentsMargins(12, 10, 12, 10)
        deck_layout.setSpacing(12)

        # Track selector row
        sel_row = QHBoxLayout()
        sel_row.setSpacing(8)

        sel_lbl = QLabel("Select Audio Track:")
        sel_lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #F5EFE6;")
        sel_row.addWidget(sel_lbl)

        self.track_combo = QComboBox()
        self.track_combo.setView(QListView())
        self.track_combo.setStyleSheet("min-width: 220px; font-size: 12px; padding: 4px 10px;")
        self.track_combo.currentIndexChanged.connect(self.on_track_selected)
        sel_row.addWidget(self.track_combo, 1)

        self.del_track_btn = QPushButton("🗑️ Delete Track")
        self.del_track_btn.setObjectName("SecondaryButton")
        self.del_track_btn.setCursor(Qt.PointingHandCursor)
        self.del_track_btn.setStyleSheet("font-size: 11px; padding: 4px 10px; color: #F87171;")
        self.del_track_btn.clicked.connect(self.delete_current_track)
        sel_row.addWidget(self.del_track_btn)

        deck_layout.addLayout(sel_row)

        # Player Controls Row (Big Play Button, Progress Slider, Timestamp)
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(10)

        self.play_btn = QPushButton("▶ Play")
        self.play_btn.setCursor(Qt.PointingHandCursor)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #8B5E3C;
                color: #FFFFFF;
                font-size: 13px;
                font-weight: bold;
                padding: 8px 18px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #A27046;
            }
        """)
        self.play_btn.clicked.connect(self.toggle_play_pause)
        ctrl_row.addWidget(self.play_btn)

        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setObjectName("SecondaryButton")
        self.stop_btn.setCursor(Qt.PointingHandCursor)
        self.stop_btn.setStyleSheet("font-size: 12px; padding: 8px 12px;")
        self.stop_btn.clicked.connect(self.stop_playback)
        ctrl_row.addWidget(self.stop_btn)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.sliderPressed.connect(self.on_slider_pressed)
        self.slider.sliderReleased.connect(self.on_slider_released)
        self.slider.sliderMoved.connect(self.on_slider_moved)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 6px;
                background: #332E28;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #D4A373;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #F5EFE6;
                width: 16px;
                margin-top: -5px;
                margin-bottom: -5px;
                border-radius: 8px;
            }
        """)
        ctrl_row.addWidget(self.slider, 1)

        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("font-size: 12px; color: #A89F91; font-family: monospace; font-weight: bold;")
        ctrl_row.addWidget(self.time_label)

        deck_layout.addLayout(ctrl_row)

        layout.addWidget(deck_card)

        # 3. Audio Info / Preview Card
        info_card = QFrame()
        info_card.setStyleSheet("""
            QFrame {
                background-color: #201D1A;
                border: 1px solid #332E28;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(10, 8, 10, 8)
        info_layout.setSpacing(6)

        info_title = QLabel("ℹ️ Track Details & Storage:")
        info_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #D4A373;")
        info_layout.addWidget(info_title)

        self.track_info_lbl = QLabel("No track selected.")
        self.track_info_lbl.setStyleSheet("font-size: 12px; color: #F5EFE6; line-height: 1.4;")
        self.track_info_lbl.setWordWrap(True)
        info_layout.addWidget(self.track_info_lbl)

        layout.addWidget(info_card)
        layout.addStretch(1)

    def load_note(self, note):
        self.stop_playback()
        self.current_note = note
        self.audio_files = note.get("audio_files", []) if note else []
        self.populate_tracks()

    def populate_tracks(self):
        self.track_combo.blockSignals(True)
        self.track_combo.clear()

        if not self.audio_files:
            self.track_combo.addItem("No audio tracks in this note")
            self.track_combo.setEnabled(False)
            self.play_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.del_track_btn.setEnabled(False)
            self.time_label.setText("00:00 / 00:00")
            self.track_info_lbl.setText("No audio tracks recorded or imported yet.\nClick '🎙️ + Record Voice' to record your meeting/voice note, or '📂 + Import Audio File' to add audio from your PC.")
        else:
            self.track_combo.setEnabled(True)
            self.play_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
            self.del_track_btn.setEnabled(True)

            for idx, item in enumerate(self.audio_files):
                dur = item.get("duration", 0) if isinstance(item, dict) else 0
                name = item.get("name", f"Voice #{idx+1}") if isinstance(item, dict) else f"Voice #{idx+1}"
                self.track_combo.addItem(f"🎵 {name} ({dur}s)", item)

            self.update_track_info()

        self.track_combo.blockSignals(False)

    def get_current_audio_file(self):
        idx = self.track_combo.currentIndex()
        if 0 <= idx < len(self.audio_files):
            return self.audio_files[idx]
        return None

    def update_track_info(self):
        item = self.get_current_audio_file()
        if item:
            path = item.get("path") if isinstance(item, dict) else item
            dur = item.get("duration", 0) if isinstance(item, dict) else 0
            name = item.get("name", "Voice Clip") if isinstance(item, dict) else "Voice Clip"
            m, s = divmod(dur, 60)
            self.track_info_lbl.setText(f"🏷️ **Track:** {name}\n⏱️ **Duration:** {m:02d}:{s:02d} ({dur} seconds)\n📁 **File Location:** `{path}`")
        else:
            self.track_info_lbl.setText("No track selected.")

    def toggle_recording(self):
        if not self.current_note:
            QMessageBox.warning(self, "Warning", "Select or create a note before recording audio.")
            return

        if not self.audio_engine.is_recording:
            self.audio_engine.start_recording()
            self.rec_btn.setText("🔴 Recording... (Click to Stop)")
            self.rec_btn.setStyleSheet("background-color: #DC2626; font-weight: bold; font-size: 12px; padding: 6px 14px;")
        else:
            path, duration = self.audio_engine.stop_recording()
            self.rec_btn.setText("🎙️ + Record Voice")
            self.rec_btn.setStyleSheet("background-color: #B91C1C; font-weight: bold; font-size: 12px; padding: 6px 14px;")
            
            audio_files = self.current_note.setdefault("audio_files", [])
            track_name = f"Voice #{len(audio_files)+1}"
            new_clip = {
                "path": path,
                "duration": duration,
                "name": track_name
            }
            audio_files.append(new_clip)

            transcript = self.audio_engine.transcribe_audio(path)
            summary = self.audio_engine.generate_summary(transcript)
            existing_tr = self.current_note.get("transcript", "")
            self.current_note["transcript"] = (existing_tr + "\n\n" + f"[{track_name}]\n" + transcript).strip()
            self.current_note["summary"] = summary

            self.load_note(self.current_note)
            self.db.add_or_update_note(self.current_note)
            self.audio_files_updated.emit(self.current_note)

    def import_audio_file(self):
        if not self.current_note:
            QMessageBox.warning(self, "Warning", "Select or create a note before adding audio.")
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

        transcript = self.audio_engine.transcribe_audio(dest_path)
        summary = self.audio_engine.generate_summary(transcript)
        existing_tr = self.current_note.get("transcript", "")
        self.current_note["transcript"] = (existing_tr + "\n\n" + f"[{track_name}]\n" + transcript).strip()
        self.current_note["summary"] = summary

        self.load_note(self.current_note)
        self.db.add_or_update_note(self.current_note)
        self.audio_files_updated.emit(self.current_note)

    def delete_current_track(self):
        item = self.get_current_audio_file()
        if not item or not self.current_note:
            return

        name = item.get("name", "this track") if isinstance(item, dict) else "this track"
        reply = QMessageBox.question(
            self, "Confirm Delete", f"Delete audio track '{name}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            target_path = item.get("path") if isinstance(item, dict) else item
            self.current_note["audio_files"] = [
                a for a in self.current_note.get("audio_files", []) 
                if (a.get("path") if isinstance(a, dict) else a) != target_path
            ]
            self.load_note(self.current_note)
            self.db.add_or_update_note(self.current_note)
            self.audio_files_updated.emit(self.current_note)

    def toggle_play_pause(self):
        item = self.get_current_audio_file()
        if not item:
            return

        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
        elif self.player.playbackState() == QMediaPlayer.PausedState:
            self.player.play()
        else:
            path = item.get("path") if isinstance(item, dict) else item
            if not path or not os.path.exists(path):
                QMessageBox.warning(self, "Warning", "Audio file not found on disk.")
                return

            self.player.setSource(QUrl.fromLocalFile(path))
            self.player.play()

    def stop_playback(self):
        self.player.stop()
        self.play_btn.setText("▶ Play")
        self.slider.setValue(0)
        self.update_time_label(0, self.player.duration())

    def on_playback_state_changed(self, state):
        if state == QMediaPlayer.PlayingState:
            self.play_btn.setText("⏸ Pause")
        else:
            self.play_btn.setText("▶ Play")

    def on_position_changed(self, position):
        if not self.is_slider_pressed:
            duration = self.player.duration()
            if duration > 0:
                self.slider.setValue(int((position / duration) * 100))
            self.update_time_label(position, duration)

    def on_duration_changed(self, duration):
        self.update_time_label(self.player.position(), duration)

    def on_slider_pressed(self):
        self.is_slider_pressed = True

    def on_slider_released(self):
        self.is_slider_pressed = False
        duration = self.player.duration()
        if duration > 0:
            new_pos = int((self.slider.value() / 100.0) * duration)
            self.player.setPosition(new_pos)

    def on_slider_moved(self, value):
        duration = self.player.duration()
        if duration > 0:
            cur_ms = int((value / 100.0) * duration)
            self.update_time_label(cur_ms, duration)

    def update_time_label(self, cur_ms, total_ms):
        cur_sec = int(cur_ms / 1000)
        tot_sec = int(total_ms / 1000) if total_ms > 0 else 0
        cur_m, cur_s = divmod(cur_sec, 60)
        tot_m, tot_s = divmod(tot_sec, 60)
        self.time_label.setText(f"{cur_m:02d}:{cur_s:02d} / {tot_m:02d}:{tot_s:02d}")

    def on_track_selected(self, index):
        self.stop_playback()
        self.update_track_info()
