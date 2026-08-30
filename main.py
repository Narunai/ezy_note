import sys
import os
import time
import ctypes
from ctypes import wintypes

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QTabWidget, QLabel, QLineEdit, QPushButton, QFrame, QMessageBox,
    QSystemTrayIcon, QMenu, QInputDialog
)
from PySide6.QtCore import Qt, QTimer, Signal, QPoint
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

# Win32 Constants for Native Windows Snap & Aero Docking
WM_NCCALCSIZE = 0x0083
WM_NCHITTEST  = 0x0084

HTCLIENT     = 1
HTCAPTION    = 2
HTLEFT       = 10
HTRIGHT      = 11
HTTOP        = 12
HTTOPLEFT    = 13
HTTOPRIGHT   = 14
HTBOTTOM     = 15
HTBOTTOMLEFT = 16
HTBOTTOMRIGHT= 17

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

        # Restore saved window position & size from previous session
        saved_geo = self.db.get_window_geometry()
        if saved_geo:
            gx = saved_geo.get("x", 100)
            gy = saved_geo.get("y", 100)
            gw = saved_geo.get("w", 1020)
            gh = saved_geo.get("h", 680)
            self.move(gx, gy)
            self.resize(gw, gh)
            self.saved_pos = QPoint(gx, gy)
            self.saved_size = self.size()
        else:
            self.saved_pos = self.pos()
            self.saved_size = self.size()

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

        # Tab 0: 📝 Notepad (Distraction-free, visible formatting bar, direct voice record)
        self.editor_tab = NoteEditorWidget(self.db, self.audio_engine)
        self.editor_tab.switch_to_voice_requested.connect(lambda: self.tabs.setCurrentIndex(1))
        self.editor_tab.audio_files_updated.connect(self.on_audio_files_updated)
        self.tabs.addTab(self.editor_tab, "📝 Notepad")

        # Tab 1: 🎙️ Voice Studio (Dedicated Studio for Audio Recording & Multi-Track Playback)
        self.voice_tab = VoiceStudioTabWidget(self.audio_engine, self.db)
        self.voice_tab.audio_files_updated.connect(self.on_audio_files_updated)
        self.tabs.addTab(self.voice_tab, "🎙️ Voice Studio")

        # Tab 2: 🤖 AI Summary (AI Meeting Summary & Topic Extraction)
        self.transcript_tab = TranscriptViewWidget(self.audio_engine, self.db)
        self.transcript_tab.transcript_updated.connect(self.on_transcript_updated)
        self.tabs.addTab(self.transcript_tab, "🤖 AI Summary")

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

    def showEvent(self, event):
        super().showEvent(event)
        try:
            hwnd = int(self.winId())
            user32 = ctypes.windll.user32
            style = user32.GetWindowLongW(hwnd, -16)  # GWL_STYLE
            # Enable WS_THICKFRAME | WS_MAXIMIZEBOX | WS_MINIMIZEBOX | WS_SYSMENU | WS_CAPTION
            style |= 0x00040000 | 0x00010000 | 0x00020000 | 0x00080000 | 0x00C00000
            user32.SetWindowLongW(hwnd, -16, style)
            user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0027)  # SWP_FRAMECHANGED | SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER
        except Exception:
            pass

    def nativeEvent(self, eventType, message):
        try:
            msg = wintypes.MSG.from_address(message.__int__())
            if msg.message == WM_NCCALCSIZE:
                # Remove default native window frame borders while preserving native Aero Snap & shadows
                return True, 0
            elif msg.message == WM_NCHITTEST:
                x = wintypes.SHORT(msg.lParam & 0xFFFF).value
                y = wintypes.SHORT((msg.lParam >> 16) & 0xFFFF).value
                pt = self.mapFromGlobal(QPoint(x, y))
                
                margin = 8
                w = self.width()
                h = self.height()
                
                # Check corners
                if pt.x() < margin and pt.y() < margin:
                    return True, HTTOPLEFT
                if pt.x() > w - margin and pt.y() < margin:
                    return True, HTTOPRIGHT
                if pt.x() < margin and pt.y() > h - margin:
                    return True, HTBOTTOMLEFT
                if pt.x() > w - margin and pt.y() > h - margin:
                    return True, HTBOTTOMRIGHT
                    
                # Check edges
                if pt.x() < margin:
                    return True, HTLEFT
                if pt.x() > w - margin:
                    return True, HTRIGHT
                if pt.y() < margin:
                    return True, HTTOP
                if pt.y() > h - margin:
                    return True, HTBOTTOM
                    
                # Check TitleBar area for native Windows Snap & Dragging
                if hasattr(self, 'title_bar') and self.title_bar.geometry().contains(pt):
                    btn_pt = self.title_bar.mapFromParent(pt)
                    child = self.title_bar.childAt(btn_pt)
                    if child and isinstance(child, QPushButton):
                        return True, HTCLIENT
                    return True, HTCAPTION
        except Exception:
            pass
        return super().nativeEvent(eventType, message)

    def toggle_window(self):
        if self.isVisible():
            # Remember exact desktop position and size
            self.saved_pos = self.pos()
            self.saved_size = self.size()
            self.db.save_window_geometry({
                "x": self.saved_pos.x(),
                "y": self.saved_pos.y(),
                "w": self.saved_size.width(),
                "h": self.saved_size.height()
            })
            self.hide()
        else:
            if hasattr(self, 'saved_pos') and self.saved_pos:
                self.move(self.saved_pos)
            if hasattr(self, 'saved_size') and self.saved_size:
                self.resize(self.saved_size)
            self.show()
            self.activateWindow()
            self.raise_()

    def on_tab_changed(self, index):
        if not self.current_note:
            return
        if index == 0:
            self.editor_tab.load_note(self.current_note)
        elif index == 1:
            self.voice_tab.load_note(self.current_note)
        elif index == 2:
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
        self.db.save_window_geometry({
            "x": self.x(),
            "y": self.y(),
            "w": self.width(),
            "h": self.height()
        })
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("NoteGod")
    
    window = NoteGodApp()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
