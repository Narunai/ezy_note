import os
import time
import shutil
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QLineEdit,
    QPushButton, QFileDialog, QRadioButton, QFrame, QMessageBox,
    QComboBox, QColorDialog, QListView, QMenu, QInputDialog
)
from PySide6.QtCore import Qt, Signal, QSize, QPoint
from PySide6.QtGui import (
    QPixmap, QIcon, QImage, QFont, QColor, QTextCursor, 
    QTextImageFormat, QAction, QKeySequence, QShortcut
)

from lightbox import ImageLightboxDialog
from database import MEDIA_DIR

class NotePaperTextEdit(QTextEdit):
    image_pasted = Signal(str)
    image_double_clicked = Signal(str, object)  # (path, cursor)
    document_modified = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptRichText(True)
        # Enable standard Notepad keyboard shortcuts
        self.setup_shortcuts()

    def setup_shortcuts(self):
        # Ctrl+B -> Bold
        QShortcut(QKeySequence.Bold, self, self.toggle_bold)
        # Ctrl+I -> Italic
        QShortcut(QKeySequence.Italic, self, self.toggle_italic)
        # Ctrl+U -> Underline
        QShortcut(QKeySequence.Underline, self, self.toggle_underline)

    def toggle_bold(self):
        fmt = self.currentCharFormat()
        weight = QFont.Normal if fmt.fontWeight() == QFont.Bold else QFont.Bold
        self.setFontWeight(weight)

    def toggle_italic(self):
        self.setFontItalic(not self.fontItalic())

    def toggle_underline(self):
        self.setFontUnderline(not self.fontUnderline())

    def insertFromMimeData(self, source):
        if source.hasImage():
            image = source.imageData()
            if isinstance(image, QImage):
                qimg = image
            else:
                qimg = QImage(image)

            if not qimg.isNull():
                os.makedirs(MEDIA_DIR, exist_ok=True)
                filename = f"paste_{int(time.time() * 1000)}.png"
                file_path = os.path.join(MEDIA_DIR, filename)
                qimg.save(file_path, "PNG")
                self.image_pasted.emit(file_path)
                return

        if source.hasUrls():
            urls = source.urls()
            for url in urls:
                path = url.toLocalFile()
                if path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp')):
                    self.image_pasted.emit(path)
                    return

        super().insertFromMimeData(source)

    def mouseDoubleClickEvent(self, event):
        cursor = self.cursorForPosition(event.pos())
        char_fmt = cursor.charFormat()
        if char_fmt.isImageFormat():
            img_fmt = char_fmt.toImageFormat()
            img_name = img_fmt.name()
            if img_name:
                self.image_double_clicked.emit(img_name, cursor)
                return
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):
        cursor = self.cursorForPosition(event.pos())
        char_fmt = cursor.charFormat()
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #201D1A;
                color: #F5EFE6;
                border: 1px solid #3D3730;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 5px 16px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #8B5E3C;
                color: #FFFFFF;
            }
        """)

        if char_fmt.isImageFormat():
            img_fmt = char_fmt.toImageFormat()
            img_path = img_fmt.name()

            view_act = menu.addAction("🔍 Open Full Lightbox (ดูภาพขนาดเต็ม)")
            view_act.triggered.connect(lambda: self.image_double_clicked.emit(img_path, cursor))

            menu.addSeparator()
            size_menu = menu.addMenu("📐 Resize Image (ปรับขนาดรูปภาพ)")
            size_menu.setStyleSheet(menu.styleSheet())

            act_180 = size_menu.addAction("Small (180px)")
            act_180.triggered.connect(lambda: self.resize_image_at_cursor(cursor, 180))

            act_260 = size_menu.addAction("Medium (260px)")
            act_260.triggered.connect(lambda: self.resize_image_at_cursor(cursor, 260))

            act_380 = size_menu.addAction("Large (380px)")
            act_380.triggered.connect(lambda: self.resize_image_at_cursor(cursor, 380))

            act_full = size_menu.addAction("Fit Width (พอดีหน้าจอ)")
            act_full.triggered.connect(lambda: self.resize_image_at_cursor(cursor, max(280, self.viewport().width() - 40)))

            act_custom = size_menu.addAction("Custom Width (กำหนดขนาดเอง)...")
            act_custom.triggered.connect(lambda: self.prompt_custom_size(cursor, int(img_fmt.width() or 240)))

            menu.addSeparator()
            del_act = menu.addAction("🗑️ Delete Image (ลบรูปภาพนี้)")
            del_act.triggered.connect(lambda: self.delete_image_at_cursor(cursor))
        else:
            # Standard Notepad Edit Options
            undo_act = menu.addAction("Undo (Ctrl+Z)")
            undo_act.triggered.connect(self.undo)
            undo_act.setEnabled(self.document().isUndoAvailable())

            redo_act = menu.addAction("Redo (Ctrl+Y)")
            redo_act.triggered.connect(self.redo)
            redo_act.setEnabled(self.document().isRedoAvailable())

            menu.addSeparator()
            cut_act = menu.addAction("Cut (Ctrl+X)")
            cut_act.triggered.connect(self.cut)
            cut_act.setEnabled(self.textCursor().hasSelection())

            copy_act = menu.addAction("Copy (Ctrl+C)")
            copy_act.triggered.connect(self.copy)
            copy_act.setEnabled(self.textCursor().hasSelection())

            paste_act = menu.addAction("Paste (Ctrl+V)")
            paste_act.triggered.connect(self.paste)

            menu.addSeparator()
            sel_all_act = menu.addAction("Select All (Ctrl+A)")
            sel_all_act.triggered.connect(self.selectAll)

        menu.exec(event.globalPos())

    def resize_image_at_cursor(self, cursor, width):
        char_fmt = cursor.charFormat()
        if char_fmt.isImageFormat():
            img_fmt = char_fmt.toImageFormat()
            img_fmt.setWidth(width)
            cursor.setCharFormat(img_fmt)
            self.document_modified.emit()

    def prompt_custom_size(self, cursor, current_w):
        val, ok = QInputDialog.getInt(self, "Custom Image Size", "Enter image width in pixels (100 - 1000):", current_w, 100, 1000, 10)
        if ok and val:
            self.resize_image_at_cursor(cursor, val)

    def delete_image_at_cursor(self, cursor):
        cursor.deleteChar()
        self.document_modified.emit()


class NoteEditorWidget(QWidget):
    note_saved = Signal(dict)
    audio_files_updated = Signal(dict)
    switch_to_voice_requested = Signal()

    def __init__(self, db, audio_engine, parent=None):
        super().__init__(parent)
        self.db = db
        self.audio_engine = audio_engine
        self.current_note = None

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(6, 4, 6, 4)
        self.layout.setSpacing(4)

        # 1. Sleek Optional Format Toolbar (Hidden by default for true Notepad minimalism)
        self.toolbar_frame = QFrame()
        self.toolbar_frame.setObjectName("FormatToolbar")
        tb_layout = QHBoxLayout(self.toolbar_frame)
        tb_layout.setContentsMargins(6, 2, 6, 2)
        tb_layout.setSpacing(5)

        self.btn_bold = QPushButton("B")
        self.btn_bold.setCheckable(True)
        self.btn_bold.setFixedSize(24, 22)
        self.btn_bold.setStyleSheet("font-weight: bold; font-size: 11px;")
        self.btn_bold.setToolTip("Bold (Ctrl+B)")
        self.btn_bold.clicked.connect(self.set_bold)
        tb_layout.addWidget(self.btn_bold)

        self.btn_italic = QPushButton("I")
        self.btn_italic.setCheckable(True)
        self.btn_italic.setFixedSize(24, 22)
        self.btn_italic.setStyleSheet("font-style: italic; font-weight: bold; font-size: 11px;")
        self.btn_italic.setToolTip("Italic (Ctrl+I)")
        self.btn_italic.clicked.connect(self.set_italic)
        tb_layout.addWidget(self.btn_italic)

        self.btn_underline = QPushButton("U")
        self.btn_underline.setCheckable(True)
        self.btn_underline.setFixedSize(24, 22)
        self.btn_underline.setStyleSheet("font-weight: bold; font-size: 11px;")
        self.btn_underline.setToolTip("Underline (Ctrl+U)")
        self.btn_underline.clicked.connect(self.set_underline)
        tb_layout.addWidget(self.btn_underline)

        font_size_label = QLabel("Size:")
        font_size_label.setStyleSheet("font-size: 11px; color: #A89F91;")
        tb_layout.addWidget(font_size_label)

        self.size_combo = QComboBox()
        self.size_combo.setView(QListView())
        self.size_combo.setStyleSheet("min-width: 48px; font-size: 11px;")
        for size in [12, 14, 16, 18, 20, 24, 28, 32]:
            self.size_combo.addItem(str(size), size)
        self.size_combo.setCurrentText("14")
        self.size_combo.currentIndexChanged.connect(self.on_size_changed)
        tb_layout.addWidget(self.size_combo)

        self.btn_color = QPushButton("Color")
        self.btn_color.setObjectName("SecondaryButton")
        self.btn_color.setStyleSheet("font-size: 11px; padding: 2px 6px; font-weight: bold;")
        self.btn_color.setToolTip("Choose Text Color")
        self.btn_color.clicked.connect(self.choose_text_color)
        tb_layout.addWidget(self.btn_color)

        div1 = QLabel("|")
        div1.setStyleSheet("color: #332E28; font-size: 12px; margin: 0 4px;")
        tb_layout.addWidget(div1)

        self.img_size_combo = QComboBox()
        self.img_size_combo.setView(QListView())
        self.img_size_combo.setStyleSheet("min-width: 85px; font-size: 11px;")
        self.img_size_combo.addItem("Small (180px)", 180)
        self.img_size_combo.addItem("Medium (240px)", 240)
        self.img_size_combo.addItem("Large (360px)", 360)
        self.img_size_combo.setCurrentIndex(1)
        tb_layout.addWidget(self.img_size_combo)

        self.add_img_btn = QPushButton("📷 + Image")
        self.add_img_btn.setObjectName("SecondaryButton")
        self.add_img_btn.setCursor(Qt.PointingHandCursor)
        self.add_img_btn.setStyleSheet("padding: 2px 6px; font-size: 11px;")
        self.add_img_btn.setToolTip("Insert image into note")
        self.add_img_btn.clicked.connect(self.upload_image)
        tb_layout.addWidget(self.add_img_btn)

        tb_layout.addStretch()

        close_tb_btn = QPushButton("✕")
        close_tb_btn.setObjectName("SecondaryButton")
        close_tb_btn.setFixedSize(20, 20)
        close_tb_btn.setStyleSheet("font-size: 10px; padding: 0px;")
        close_tb_btn.setToolTip("Hide toolbar")
        close_tb_btn.clicked.connect(lambda: self.toolbar_frame.hide())
        tb_layout.addWidget(close_tb_btn)

        self.toolbar_frame.hide()  # Hidden by default for clean Notepad feel
        self.layout.addWidget(self.toolbar_frame)

        # 2. Notepad Paper Canvas (Fills entire height smoothly)
        self.text_edit = NotePaperTextEdit()
        self.text_edit.setObjectName("NotePaperEdit")
        self.text_edit.setPlaceholderText("Start typing your note here... (Paste Ctrl+V to add images)")
        self.text_edit.image_pasted.connect(self.on_image_pasted)
        self.text_edit.image_double_clicked.connect(self.open_lightbox)
        self.text_edit.document_modified.connect(self.on_document_modified)
        self.text_edit.cursorPositionChanged.connect(self.update_status_bar)
        self.text_edit.textChanged.connect(self.update_status_bar)

        self.layout.addWidget(self.text_edit, 1)

        # 3. Minimalist Notepad Status Bar at Bottom (Slim, Non-intrusive)
        status_bar = QFrame()
        status_bar.setStyleSheet("background-color: transparent; padding: 0px 4px;")
        sb_layout = QHBoxLayout(status_bar)
        sb_layout.setContentsMargins(4, 1, 4, 1)
        sb_layout.setSpacing(8)

        self.status_lbl = QLabel("Ln 1, Col 1 | 0 words")
        self.status_lbl.setStyleSheet("color: #78716C; font-size: 10px;")
        sb_layout.addWidget(self.status_lbl)

        sb_layout.addStretch()

        self.tool_toggle_btn = QPushButton("🛠️ Tools")
        self.tool_toggle_btn.setObjectName("SecondaryButton")
        self.tool_toggle_btn.setCursor(Qt.PointingHandCursor)
        self.tool_toggle_btn.setStyleSheet("font-size: 10px; padding: 1px 6px;")
        self.tool_toggle_btn.setToolTip("Toggle Text Formatting & Image Bar")
        self.tool_toggle_btn.clicked.connect(self.toggle_toolbar)
        sb_layout.addWidget(self.tool_toggle_btn)

        self.quick_mic_btn = QPushButton("🎙️ Voice")
        self.quick_mic_btn.setObjectName("SecondaryButton")
        self.quick_mic_btn.setCursor(Qt.PointingHandCursor)
        self.quick_mic_btn.setStyleSheet("font-size: 10px; padding: 1px 6px; color: #F59E0B;")
        self.quick_mic_btn.setToolTip("Switch to Voice Studio")
        self.quick_mic_btn.clicked.connect(self.switch_to_voice_requested.emit)
        sb_layout.addWidget(self.quick_mic_btn)

        self.layout.addWidget(status_bar)

    def toggle_toolbar(self):
        if self.toolbar_frame.isVisible():
            self.toolbar_frame.hide()
        else:
            self.toolbar_frame.show()

    def update_status_bar(self):
        cursor = self.text_edit.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        text = self.text_edit.toPlainText().strip()
        words = len(text.split()) if text else 0
        chars = len(text)
        self.status_lbl.setText(f"Ln {line}, Col {col} | {words} words | {chars} chars")

    def set_bold(self):
        is_bold = self.btn_bold.isChecked()
        self.text_edit.setFontWeight(QFont.Bold if is_bold else QFont.Normal)

    def set_italic(self):
        self.text_edit.setFontItalic(self.btn_italic.isChecked())

    def set_underline(self):
        self.text_edit.setFontUnderline(self.btn_underline.isChecked())

    def on_size_changed(self, index):
        size = self.size_combo.currentData()
        if size and float(size) > 0:
            self.text_edit.setFontPointSize(float(size))

    def choose_text_color(self):
        color = QColorDialog.getColor(Qt.black, self, "Select Text Color")
        if color.isValid():
            self.text_edit.setTextColor(color)

    def load_note(self, note):
        self.current_note = note
        html = note.get("content_html") or note.get("content", "")
        self.text_edit.setHtml(html)
        self.update_status_bar()

    def get_current_data(self):
        if not self.current_note:
            self.current_note = {}
        
        self.current_note["content"] = self.text_edit.toPlainText()
        self.current_note["content_html"] = self.text_edit.toHtml()
        return self.current_note

    def upload_image(self):
        if not self.current_note:
            QMessageBox.warning(self, "Warning", "Select or create a note before adding images.")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Image to Insert", "", "Image Files (*.png *.jpg *.jpeg *.webp *.gif *.bmp)"
        )
        if file_path:
            os.makedirs(MEDIA_DIR, exist_ok=True)
            ext = os.path.splitext(file_path)[1]
            dest_filename = f"img_{int(time.time() * 1000)}{ext}"
            dest_path = os.path.join(MEDIA_DIR, dest_filename)
            shutil.copy2(file_path, dest_path)
            self.on_image_pasted(dest_path)

    def on_image_pasted(self, file_path):
        if not self.current_note:
            return

        cursor = self.text_edit.textCursor()
        img_w = self.img_size_combo.currentData() or 240

        fmt = QTextImageFormat()
        fmt.setName(file_path)
        fmt.setWidth(img_w)

        cursor.insertImage(fmt)
        cursor.insertBlock()

        self.text_edit.setTextCursor(cursor)
        self.text_edit.setFocus()
        self.on_document_modified()

    def on_document_modified(self):
        if self.current_note:
            self.current_note["content"] = self.text_edit.toPlainText()
            self.current_note["content_html"] = self.text_edit.toHtml()
            self.db.add_or_update_note(self.current_note)
            self.note_saved.emit(self.current_note)

    def open_lightbox(self, image_path, cursor=None):
        dlg = ImageLightboxDialog(image_path, "Embedded Note Image", "Document Image", self)
        if cursor is not None:
            dlg.size_selected.connect(lambda w: self.text_edit.resize_image_at_cursor(cursor, w))
        dlg.exec()
