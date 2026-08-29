import os
import time
import threading
import numpy as np

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, 
    QComboBox, QSlider, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, Signal

HAS_SOUNDDEVICE = False
try:
    import sounddevice as sd
    import soundfile as sf
    HAS_SOUNDDEVICE = True
except Exception:
    pass

class AudioPlayerWorker(threading.Thread):
    def __init__(self, audio_path, on_progress, on_finished):
        super().__init__(daemon=True)
        self.audio_path = audio_path
        self.on_progress = on_progress
        self.on_finished = on_finished
        self.is_playing = False
        self.is_paused = False
        self.stop_requested = False
        self.current_frame = 0
        self.total_frames = 0
        self.data = None
        self.samplerate = 44100

    def run(self):
        if not HAS_SOUNDDEVICE or not os.path.exists(self.audio_path):
            self.on_finished()
            return

        try:
            self.data, self.samplerate = sf.read(self.audio_path, dtype='float32')
            self.total_frames = len(self.data)
            self.is_playing = True

            blocksize = 2048
            
            with sd.OutputStream(samplerate=self.samplerate, channels=self.data.shape[1] if self.data.ndim > 1 else 1) as stream:
                while self.current_frame < self.total_frames and not self.stop_requested:
                    if self.is_paused:
                        time.sleep(0.05)
                        continue
                    
                    chunk = self.data[self.current_frame:self.current_frame + blocksize]
                    stream.write(chunk)
                    self.current_frame += len(chunk)
                    
                    progress = int((self.current_frame / self.total_frames) * 100)
                    self.on_progress(progress, int(self.current_frame / self.samplerate), int(self.total_frames / self.samplerate))
                    
        except Exception as e:
            print("In-app playback error:", e)
        finally:
            self.is_playing = False
            self.on_finished()

class InAppAudioPlayerWidget(QWidget):
    recording_requested = Signal()
    audio_deleted = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.audio_files = []
        self.current_worker = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(4)

        # Control Bar 1: Track selector & Record button
        top_row = QHBoxLayout()
        top_row.setSpacing(6)

        track_label = QLabel("Audio Tracks:")
        track_label.setStyleSheet("font-weight: bold; font-size: 11px; color: #D4A373;")
        top_row.addWidget(track_label)

        self.track_combo = QComboBox()
        self.track_combo.setStyleSheet("""
            QComboBox {
                background-color: #161412;
                border: 1px solid #332E28;
                border-radius: 4px;
                padding: 2px 6px;
                color: #F5EFE6;
                font-size: 11px;
                min-width: 140px;
            }
        """)
        self.track_combo.currentIndexChanged.connect(self.on_track_selected)
        top_row.addWidget(self.track_combo, 1)

        self.rec_btn = QPushButton("+ Record Voice")
        self.rec_btn.setStyleSheet("background-color: #B91C1C; font-weight: bold; font-size: 11px; padding: 3px 8px;")
        self.rec_btn.clicked.connect(self.recording_requested.emit)
        top_row.addWidget(self.rec_btn)

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
                dur = item.get("duration", 0)
                name = item.get("name", f"Voice #{idx+1}")
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

        if self.current_worker and self.current_worker.is_playing:
            if self.current_worker.is_paused:
                self.current_worker.is_paused = False
                self.play_btn.setText("Pause")
            else:
                self.current_worker.is_paused = True
                self.play_btn.setText("Play")
        else:
            path = item.get("path")
            if not path or not os.path.exists(path):
                QMessageBox.warning(self, "Warning", "Audio file not found.")
                return

            self.play_btn.setText("Pause")
            self.current_worker = AudioPlayerWorker(
                path,
                on_progress=self.update_progress,
                on_finished=self.on_playback_finished
            )
            self.current_worker.start()

    def stop_playback(self):
        if self.current_worker:
            self.current_worker.stop_requested = True
            self.current_worker = None
        self.play_btn.setText("Play")
        self.slider.setValue(0)

    def update_progress(self, progress, cur_sec, total_sec):
        self.slider.setValue(progress)
        cur_m, cur_s = divmod(cur_sec, 60)
        tot_m, tot_s = divmod(total_sec, 60)
        self.time_label.setText(f"{cur_m:02d}:{cur_s:02d} / {tot_m:02d}:{tot_s:02d}")

    def on_playback_finished(self):
        self.play_btn.setText("Play")

    def on_track_selected(self, index):
        self.stop_playback()

    def delete_current_track(self):
        item = self.get_current_audio_file()
        if item:
            self.audio_deleted.emit(item)
