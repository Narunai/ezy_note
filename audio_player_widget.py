import os
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, 
    QComboBox, QSlider, QListView, QMessageBox
)
from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

class InAppAudioPlayerWidget(QWidget):
    recording_requested = Signal()
    import_requested = Signal()
    audio_deleted = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.audio_files = []
        self.is_slider_pressed = False

        # Initialize QMediaPlayer & AudioOutput for native multi-format support
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(1.0)

        self.player.positionChanged.connect(self.on_position_changed)
        self.player.durationChanged.connect(self.on_duration_changed)
        self.player.playbackStateChanged.connect(self.on_playback_state_changed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(4)

        # Control Bar 1: Track selector & Record / Import button
        top_row = QHBoxLayout()
        top_row.setSpacing(6)

        track_label = QLabel("Audio Tracks:")
        track_label.setStyleSheet("font-weight: bold; font-size: 11px; color: #D4A373;")
        top_row.addWidget(track_label)

        self.track_combo = QComboBox()
        self.track_combo.setView(QListView())
        self.track_combo.setStyleSheet("min-width: 140px;")
        self.track_combo.currentIndexChanged.connect(self.on_track_selected)
        top_row.addWidget(self.track_combo, 1)

        self.rec_btn = QPushButton("+ Record Voice")
        self.rec_btn.setStyleSheet("background-color: #B91C1C; font-weight: bold; font-size: 11px; padding: 3px 8px;")
        self.rec_btn.clicked.connect(self.recording_requested.emit)
        top_row.addWidget(self.rec_btn)

        self.import_btn = QPushButton("+ Add File")
        self.import_btn.setObjectName("SecondaryButton")
        self.import_btn.setToolTip("Import Audio File from Computer (.mp3, .wav, .m4a, .flac, .ogg)")
        self.import_btn.setStyleSheet("font-size: 11px; padding: 3px 8px;")
        self.import_btn.clicked.connect(self.import_requested.emit)
        top_row.addWidget(self.import_btn)

        self.del_track_btn = QPushButton("Delete")
        self.del_track_btn.setObjectName("SecondaryButton")
        self.del_track_btn.setStyleSheet("font-size: 10px; padding: 2px 6px;")
        self.del_track_btn.clicked.connect(self.delete_current_track)
        top_row.addWidget(self.del_track_btn)

        layout.addLayout(top_row)

        # Control Bar 2: In-App Player Controls (Play, Slider, Timer)
        player_row = QHBoxLayout()
        player_row.setSpacing(8)

        self.play_btn = QPushButton("Play")
        self.play_btn.setCursor(Qt.PointingHandCursor)
        self.play_btn.setStyleSheet("font-weight: bold; font-size: 11px; padding: 3px 12px; background-color: #8B5E3C;")
        self.play_btn.clicked.connect(self.toggle_play_pause)
        player_row.addWidget(self.play_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setObjectName("SecondaryButton")
        self.stop_btn.setStyleSheet("font-size: 10px; padding: 3px 8px;")
        self.stop_btn.clicked.connect(self.stop_playback)
        player_row.addWidget(self.stop_btn)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.sliderPressed.connect(self.on_slider_pressed)
        self.slider.sliderReleased.connect(self.on_slider_released)
        self.slider.sliderMoved.connect(self.on_slider_moved)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px;
                background: #332E28;
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: #D4A373;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #F5EFE6;
                width: 12px;
                margin-top: -4px;
                margin-bottom: -4px;
                border-radius: 6px;
            }
        """)
        player_row.addWidget(self.slider, 1)

        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("font-size: 10px; color: #A89F91; font-family: monospace;")
        player_row.addWidget(self.time_label)

        layout.addLayout(player_row)

    def load_audio_files(self, audio_files):
        self.stop_playback()
        self.audio_files = audio_files if audio_files else []
        self.track_combo.blockSignals(True)
        self.track_combo.clear()

        if not self.audio_files:
            self.track_combo.addItem("No audio tracks")
            self.track_combo.setEnabled(False)
            self.play_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.del_track_btn.setEnabled(False)
            self.time_label.setText("00:00 / 00:00")
        else:
            self.track_combo.setEnabled(True)
            self.play_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
            self.del_track_btn.setEnabled(True)

            for idx, item in enumerate(self.audio_files):
                dur = item.get("duration", 0) if isinstance(item, dict) else 0
                name = item.get("name", f"Voice #{idx+1}") if isinstance(item, dict) else f"Voice #{idx+1}"
                self.track_combo.addItem(f"{name} ({dur}s)")

        self.track_combo.blockSignals(False)

    def get_current_audio_file(self):
        idx = self.track_combo.currentIndex()
        if 0 <= idx < len(self.audio_files):
            return self.audio_files[idx]
        return None

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
        self.play_btn.setText("Play")
        self.slider.setValue(0)
        self.update_time_label(0, self.player.duration())

    def on_playback_state_changed(self, state):
        if state == QMediaPlayer.PlayingState:
            self.play_btn.setText("Pause")
        else:
            self.play_btn.setText("Play")

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

    def delete_current_track(self):
        item = self.get_current_audio_file()
        if item:
            self.audio_deleted.emit(item)
