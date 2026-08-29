from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QListWidget, QListWidgetItem, QPushButton, QFrame, QMenu,
    QInputDialog, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
import datetime

class SidebarWidget(QWidget):
    note_selected = Signal(dict)
    new_note_requested = Signal()
    toggle_collapse_requested = Signal(bool)
    delete_note_requested = Signal(str)
    rename_note_requested = Signal(dict, str) # note_id, new_title

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setObjectName("SidebarWidget")
        self.setFixedWidth(190)
        self.is_collapsed = False

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(6, 8, 6, 8)
        self.layout.setSpacing(6)

        # Header area
        header_frame = QFrame()
        header_frame.setObjectName("SidebarHeader")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 4)
        header_layout.setSpacing(4)

        title_row = QHBoxLayout()
        self.title_label = QLabel("Notes History")
        self.title_label.setObjectName("SidebarTitle")
        title_row.addWidget(self.title_label)
        title_row.addStretch()

        # Hide / Toggle Sidebar Button
        self.collapse_btn = QPushButton("Hide")
        self.collapse_btn.setObjectName("SecondaryButton")
        self.collapse_btn.setStyleSheet("font-size: 10px; padding: 2px 6px;")
        self.collapse_btn.setToolTip("Hide / Show Sidebar")
        self.collapse_btn.clicked.connect(self.toggle_collapsed)
        title_row.addWidget(self.collapse_btn)

        header_layout.addLayout(title_row)

        # New note button
        self.new_btn = QPushButton("+ New Note")
        self.new_btn.setCursor(Qt.PointingHandCursor)
        self.new_btn.clicked.connect(self.new_note_requested.emit)
        header_layout.addWidget(self.new_btn)

        self.layout.addWidget(header_frame)

        # Search bar
        self.search_box = QLineEdit()
        self.search_box.setObjectName("SearchBox")
        self.search_box.setPlaceholderText("Search notes...")
        self.search_box.textChanged.connect(self.filter_notes)
        self.layout.addWidget(self.search_box)

        # Note history list with Custom Context Menu (Right Click)
        self.list_widget = QListWidget()
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.open_context_menu)
        self.list_widget.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
            }
            QListWidget::item {
                background-color: #161412;
                border-radius: 6px;
                padding: 6px;
                margin-bottom: 4px;
                color: #F5EFE6;
                font-size: 11px;
            }
            QListWidget::item:hover {
                background-color: #332E28;
                border: 1px solid #D4A373;
            }
            QListWidget::item:selected {
                background-color: #8B5E3C;
                border: 1px solid #D4A373;
            }
        """)
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        self.layout.addWidget(self.list_widget, 1)

        self.refresh_notes()

    def toggle_collapsed(self):
        self.is_collapsed = not self.is_collapsed
        if self.is_collapsed:
            self.hide()
        else:
            self.show()
        
        self.toggle_collapse_requested.emit(self.is_collapsed)

    def refresh_notes(self):
        self.list_widget.clear()
        notes = self.db.get_all_notes()
        filter_text = self.search_box.text().strip().lower()

        for note in notes:
            title = note.get("title", "Untitled Note")
            content = note.get("content", "")
            updated_at = note.get("updated_at", 0)

            if filter_text and (filter_text not in title.lower() and filter_text not in content.lower()):
                continue

            dt_str = ""
            if updated_at:
                dt = datetime.datetime.fromtimestamp(updated_at)
                dt_str = dt.strftime("%H:%M")

            display_title = title if len(title) <= 16 else title[:14] + "..."

            media_icons = ""
            if note.get("images"):
                media_icons += "[Img] "
            if note.get("audio_files") or note.get("audio_path"):
                media_icons += "[Rec] "

            item_text = f"{media_icons}{display_title}\nTime: {dt_str}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, note.get("id"))
            self.list_widget.addItem(item)

    def filter_notes(self):
        self.refresh_notes()

    def on_item_clicked(self, item):
        note_id = item.data(Qt.UserRole)
        note = self.db.get_note_by_id(note_id)
        if note:
            self.note_selected.emit(note)

    def select_note_by_id(self, note_id):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.UserRole) == note_id:
                self.list_widget.setCurrentItem(item)
                break

    def open_context_menu(self, position):
        item = self.list_widget.itemAt(position)
        if not item:
            return

        note_id = item.data(Qt.UserRole)
        note = self.db.get_note_by_id(note_id)
        if not note:
            return

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #201D1A;
                color: #F5EFE6;
                border: 1px solid #332E28;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item:selected {
                background-color: #8B5E3C;
                color: #FFFFFF;
                border-radius: 4px;
            }
        """)

        rename_action = QAction("Rename Note", self)
        rename_action.triggered.connect(lambda: self.rename_note_dialog(note))
        menu.addAction(rename_action)

        delete_action = QAction("Delete Note", self)
        delete_action.triggered.connect(lambda: self.delete_note_requested.emit(note_id))
        menu.addAction(delete_action)

        menu.exec(self.list_widget.mapToGlobal(position))

    def rename_note_dialog(self, note):
        old_title = note.get("title", "")
        new_title, ok = QInputDialog.getText(self, "Rename Note", "Enter new note title:", QLineEdit.Normal, old_title)
        if ok and new_title.strip():
            self.rename_note_requested.emit(note, new_title.strip())
