import sys
import os
import time

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QTabWidget, QLabel, QLineEdit, QPushButton, QFrame, QMessageBox,
    QSystemTrayIcon, QMenu, QInputDialog
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QIcon, QFont, QAction, QColor

from database import NoteDatabase, MEDIA_DIR, DATA_DIR
from style import QSS_STYLE
from sidebar_widget import SidebarWidget
from note_editor import NoteEditorWidget
from transcript_view import TranscriptViewWidget
from audio_player_widget import VoiceStudioTabWidget
from audio_engine import AudioEngine
from floating_widget import FloatingNoteWidget
from custom_titlebar import CustomTitleBar

class NoteGodApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.resize(1020, 680)
        self.setMinimumSize(360, 420)
        self.setMouseTracking(True)

        # Initialize Database & Audio Engine
        self.db = NoteDatabase()
        self.audio_engine = AudioEngine(MEDIA_DIR)
        self.current_note = None

        # Apply stylesheet
        self.setStyleSheet(QSS_STYLE)

        # Root Outer Container with Custom TitleBar
        root_widget = QWidget()
        root_widget.setMouseTracking(True)
        self.setCentralWidget(root_widget)
        root_layout = QVBoxLayout(root_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Custom Minimalist TitleBar (supports Windows Snap & Drag)
        self.title_bar = CustomTitleBar(self)
        root_layout.addWidget(self.title_bar)

        # Main Layout Container
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        root_layout.addWidget(main_widget, 1)

        # 1. Sidebar Widget
        self.sidebar = SidebarWidget(self.db)
        self.sidebar.note_selected.connect(self.on_note_selected)
        self.sidebar.new_note_requested.connect(self.create_new_note)
        self.sidebar.delete_note_requested.connect(self.delete_note_by_id)
        self.sidebar.rename_note_requested.connect(self.rename_note_by_obj)
        main_layout.addWidget(self.sidebar)

        # 2. Main Content Area
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(6, 6, 6, 6)
        content_layout.setSpacing(4)

        # Top Action Bar
        top_bar = QFrame()
        top_bar.setObjectName("EditorHeader")
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(8, 2, 8, 2)
        top_bar_layout.setSpacing(6)

        self.toggle_sidebar_btn = QPushButton("Sidebar")
        self.toggle_sidebar_btn.setObjectName("SecondaryButton")
        self.toggle_sidebar_btn.setToolTip("Toggle Sidebar")
        self.toggle_sidebar_btn.clicked.connect(self.sidebar.toggle_collapsed)
        top_bar_layout.addWidget(self.toggle_sidebar_btn)

        self.title_input = QLineEdit()
        self.title_input.setObjectName("TitleInput")
        self.title_input.setPlaceholderText("Note Title...")
        self.title_input.textChanged.connect(self.on_title_changed)
        top_bar_layout.addWidget(self.title_input, 1)

        self.rename_btn = QPushButton("Rename")
        self.rename_btn.setObjectName("SecondaryButton")
        self.rename_btn.setToolTip("Rename Note Title")
        self.rename_btn.clicked.connect(self.on_rename_clicked)
        top_bar_layout.addWidget(self.rename_btn)

        self.save_status_label = QLabel("[Saved]")
        self.save_status_label.setStyleSheet("color: #10B981; font-size: 11px; font-weight: bold;")
        top_bar_layout.addWidget(self.save_status_label)

        self.open_folder_btn = QPushButton("Folder")
        self.open_folder_btn.setObjectName("SecondaryButton")
        self.open_folder_btn.setToolTip("Open Storage Folder")
        self.open_folder_btn.clicked.connect(self.open_data_folder)
        top_bar_layout.addWidget(self.open_folder_btn)

        self.save_btn = QPushButton("Save")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.clicked.connect(self.save_current_note)
        top_bar_layout.addWidget(self.save_btn)

        self.del_btn = QPushButton("Delete")
        self.del_btn.setObjectName("DangerButton")
        self.del_btn.setCursor(Qt.PointingHandCursor)
        self.del_btn.clicked.connect(self.delete_current_note)
        top_bar_layout.addWidget(self.del_btn)

        content_layout.addWidget(top_bar)

        # 3 Dedicated Tabs Widget
        self.tabs = QTabWidget()

        # Tab 0: 📝 Note Paper (Maximum height, uncluttered, Word/Teams image integration)
        self.editor_tab = NoteEditorWidget(self.db, self.audio_engine)
        self.editor_tab.switch_to_voice_requested.connect(lambda: self.tabs.setCurrentIndex(1))
        self.tabs.addTab(self.editor_tab, "📝 Note Paper")

        # Tab 1: 🎙️ Voice & Audio Studio (Dedicated Studio for Audio Recording & Multi-Track Playback)
        self.voice_tab = VoiceStudioTabWidget(self.audio_engine, self.db)
        self.voice_tab.audio_files_updated.connect(self.on_audio_files_updated)
        self.tabs.addTab(self.voice_tab, "🎙️ Voice Studio")

        # Tab 2: 🤖 Transcript & AI Summary (AI Meeting Summary & Topic Extraction)
        self.transcript_tab = TranscriptViewWidget(self.audio_engine, self.db)
        self.transcript_tab.transcript_updated.connect(self.on_transcript_updated)
        self.tabs.addTab(self.transcript_tab, "🤖 Transcript & AI Summary")

        self.tabs.currentChanged.connect(self.on_tab_changed)

        content_layout.addWidget(self.tabs, 1)
        main_layout.addWidget(content_area, 1)

        # 4. Create Floating Desktop Note Widget
        self.floating_widget = FloatingNoteWidget()
        self.floating_widget.clicked.connect(self.toggle_window)

        screen = QApplication.primaryScreen().geometry()
        self.floating_widget.move(screen.width() - 80, 100)
        self.floating_widget.show()

        # Load initial note
        notes = self.db.get_all_notes()
        if notes:
            self.on_note_selected(notes[0])
            self.sidebar.select_note_by_id(notes[0]["id"])
        else:
            self.create_new_note()

        # Auto-save timer (every 5 seconds)
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self.auto_save)
        self.auto_save_timer.start(5000)

    def get_resize_edge(self, pos):
        margin = 8
        edge = Qt.Edge(0)
        w = self.width()
        h = self.height()
        if pos.x() <= margin:
            edge |= Qt.LeftEdge
        elif pos.x() >= w - margin:
            edge |= Qt.RightEdge
        if pos.y() <= margin:
            edge |= Qt.TopEdge
        elif pos.y() >= h - margin:
            edge |= Qt.BottomEdge
        return edge

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
            edge = self.get_resize_edge(pos)
            if edge != Qt.Edge(0):
                wh = self.windowHandle()
                if wh and wh.startSystemResize(edge):
                    event.accept()
                    return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
        edge = self.get_resize_edge(pos)
        if edge in (Qt.LeftEdge | Qt.TopEdge, Qt.RightEdge | Qt.BottomEdge):
            self.setCursor(Qt.SizeFDiagCursor)
        elif edge in (Qt.RightEdge | Qt.TopEdge, Qt.LeftEdge | Qt.BottomEdge):
            self.setCursor(Qt.SizeBDiagCursor)
        elif edge in (Qt.LeftEdge, Qt.RightEdge):
            self.setCursor(Qt.SizeHorCursor)
        elif edge in (Qt.TopEdge, Qt.BottomEdge):
            self.setCursor(Qt.SizeVerCursor)
        else:
            self.unsetCursor()
        super().mouseMoveEvent(event)

    def toggle_window(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.activateWindow()

    def on_tab_changed(self, index):
        if not self.current_note:
            return
        if index == 0:
            # Switched to Note Paper
            self.editor_tab.load_note(self.current_note)
        elif index == 1:
            # Switched to Voice Studio
            self.voice_tab.load_note(self.current_note)
        elif index == 2:
            # Switched to Transcript & AI Summary
            self.transcript_tab.load_note(self.current_note)

    def on_audio_files_updated(self, note):
        self.current_note = note
        self.voice_tab.load_note(note)
        self.transcript_tab.load_note(note)
        self.sidebar.refresh_notes()

    def on_transcript_updated(self, note):
        self.current_note = note
        self.sidebar.refresh_notes()

    def on_note_selected(self, note):
        self.save_current_note()
        self.current_note = note
        self.title_input.setText(note.get("title", ""))
        self.editor_tab.load_note(note)
        self.voice_tab.load_note(note)
        self.transcript_tab.load_note(note)
        self.save_status_label.setText("[Saved]")

    def create_new_note(self):
        self.save_current_note()
        new_note = self.db.add_or_update_note({
            "title": "Untitled Note",
            "content": "",
            "images": [],
            "image_position": "inline",
            "audio_path": "",
            "audio_duration": 0,
            "audio_files": [],
            "transcript": "",
            "summary": ""
        })
        self.sidebar.refresh_notes()
        self.on_note_selected(new_note)
        self.sidebar.select_note_by_id(new_note["id"])

    def on_title_changed(self, text):
        if self.current_note:
            self.current_note["title"] = text
            self.save_status_label.setText("[Saving...]")

    def save_current_note(self):
        if not self.current_note:
            return

        editor_data = self.editor_tab.get_current_data()
        self.current_note["title"] = self.title_input.text() or "Untitled Note"
        if editor_data:
            self.current_note["content"] = editor_data.get("content", "")
            self.current_note["content_html"] = editor_data.get("content_html", "")
            self.current_note["image_position"] = editor_data.get("image_position", "inline")
            if "images" in editor_data:
                self.current_note["images"] = editor_data.get("images", [])

        transcript_data = self.transcript_tab.get_updated_data()
        if transcript_data:
            tr = transcript_data.get("transcript")
            sm = transcript_data.get("summary")
            if tr or self.tabs.currentIndex() == 2:
                self.current_note["transcript"] = tr or ""
            if sm or self.tabs.currentIndex() == 2:
                self.current_note["summary"] = sm or ""

        saved_note = self.db.add_or_update_note(self.current_note)
        self.sidebar.refresh_notes()
        self.save_status_label.setText("[Saved]")

    def on_rename_clicked(self):
        if not self.current_note:
            return
        old_title = self.current_note.get("title", "")
        new_title, ok = QInputDialog.getText(self, "Rename Note", "Enter new title:", QLineEdit.Normal, old_title)
        if ok and new_title.strip():
            self.rename_note_by_obj(self.current_note, new_title.strip())

    def rename_note_by_obj(self, note, new_title):
        note["title"] = new_title
        if self.current_note and self.current_note.get("id") == note.get("id"):
            self.title_input.setText(new_title)
        self.db.add_or_update_note(note)
        self.sidebar.refresh_notes()

    def delete_current_note(self):
        if self.current_note:
            self.delete_note_by_id(self.current_note["id"])

    def delete_note_by_id(self, note_id):
        note = self.db.get_note_by_id(note_id)
        title = note.get("title", "this note") if note else "this note"
        reply = QMessageBox.question(
            self, "Confirm Delete", f"Delete note '{title}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db.delete_note(note_id)
            self.sidebar.refresh_notes()
            notes = self.db.get_all_notes()
            if notes:
                self.on_note_selected(notes[0])
            else:
                self.create_new_note()

    def open_data_folder(self):
        try:
            os.startfile(DATA_DIR)
        except Exception as e:
            QMessageBox.information(self, "Data Directory", f"Storage Folder:\n{DATA_DIR}")

    def auto_save(self):
        if self.current_note:
            self.save_current_note()

    def closeEvent(self, event):
        self.save_current_note()
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("NoteGod")
    
    window = NoteGodApp()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
