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
    QTextImageFormat, QAction
)

from lightbox import ImageLightboxDialog
from database import MEDIA_DIR
from audio_player_widget import InAppAudioPlayerWidget

class NotePaperTextEdit(QTextEdit):
    image_pasted = Signal(str)
    image_double_clicked = Signal(str, object)  # (path, cursor)
    document_modified = Signal()

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
        
        if char_fmt.isImageFormat():
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
                    padding: 6px 16px;
                    border-radius: 4px;
                }
                QMenu::item:selected {
                    background-color: #8B5E3C;
                    color: #FFFFFF;
                }
            """)
            img_fmt = char_fmt.toImageFormat()
            img_path = img_fmt.name()

            view_act = menu.addAction("🔍 Open Full Lightbox (ดูภาพขนาดเต็ม)")
            view_act.triggered.connect(lambda: self.image_double_clicked.emit(img_path, cursor))

            menu.addSeparator()
            size_menu = menu.addMenu("📐 Resize Image (ปรับขนาดรูปภาพ)")
            size_menu.setStyleSheet(menu.styleSheet())

            act_200 = size_menu.addAction("Small (200px)")
            act_200.triggered.connect(lambda: self.resize_image_at_cursor(cursor, 200))

            act_320 = size_menu.addAction("Medium (320px)")
            act_320.triggered.connect(lambda: self.resize_image_at_cursor(cursor, 320))

            act_480 = size_menu.addAction("Large (480px)")
            act_480.triggered.connect(lambda: self.resize_image_at_cursor(cursor, 480))

            act_full = size_menu.addAction("Fit Width (พอดีความกว้าง)")
            act_full.triggered.connect(lambda: self.resize_image_at_cursor(cursor, max(300, self.viewport().width() - 40)))

            act_custom = size_menu.addAction("Custom Width (กำหนดขนาดเอง)...")
            act_custom.triggered.connect(lambda: self.prompt_custom_size(cursor, int(img_fmt.width() or 320)))

            menu.addSeparator()
            del_act = menu.addAction("🗑️ Delete Image (ลบรูปภาพนี้)")
            del_act.triggered.connect(lambda: self.delete_image_at_cursor(cursor))

            menu.exec(event.globalPos())
            return

        super().contextMenuEvent(event)

    def resize_image_at_cursor(self, cursor, width):
        char_fmt = cursor.charFormat()
        if char_fmt.isImageFormat():
            img_fmt = char_fmt.toImageFormat()
            img_fmt.setWidth(width)
            cursor.setCharFormat(img_fmt)
            self.document_modified.emit()

    def prompt_custom_size(self, cursor, current_w):
        val, ok = QInputDialog.getInt(self, "Custom Image Size", "Enter image width in pixels (100 - 1200):", current_w, 100, 1200, 10)
        if ok and val:
            self.resize_image_at_cursor(cursor, val)

    def delete_image_at_cursor(self, cursor):
        cursor.deleteChar()
        self.document_modified.emit()


class NoteEditorWidget(QWidget):
    note_saved = Signal(dict)
    audio_files_updated = Signal(dict)

    def __init__(self, db, audio_engine, parent=None):
        super().__init__(parent)
        self.db = db
        self.audio_engine = audio_engine
        self.current_note = None

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(6, 6, 6, 6)
        self.layout.setSpacing(6)

        # Image Placement & Sizing Control Banner
        pos_bar = QFrame()
        pos_bar.setObjectName("ImagePosBanner")
        pos_layout = QHBoxLayout(pos_bar)
        pos_layout.setContentsMargins(8, 2, 8, 2)
        pos_layout.setSpacing(8)

        pos_label = QLabel("Image Placement:")
        pos_label.setStyleSheet("font-weight: bold; color: #D4A373; font-size: 11px;")
        pos_layout.addWidget(pos_label)

        self.radio_top = QRadioButton("Above")
        self.radio_inline = QRadioButton("Inline (At Cursor)")
        self.radio_bottom = QRadioButton("Below")

        self.radio_top.setStyleSheet("font-size: 11px;")
        self.radio_inline.setStyleSheet("font-size: 11px;")
        self.radio_bottom.setStyleSheet("font-size: 11px;")

        self.radio_inline.setChecked(True)

        self.radio_top.toggled.connect(self.on_image_pos_changed)
        self.radio_inline.toggled.connect(self.on_image_pos_changed)
        self.radio_bottom.toggled.connect(self.on_image_pos_changed)

        pos_layout.addWidget(self.radio_inline)
        pos_layout.addWidget(self.radio_top)
        pos_layout.addWidget(self.radio_bottom)

        size_label = QLabel("Size:")
        size_label.setStyleSheet("font-weight: bold; color: #D4A373; font-size: 11px; margin-left: 6px;")
        pos_layout.addWidget(size_label)

        self.img_size_combo = QComboBox()
        self.img_size_combo.setView(QListView())
        self.img_size_combo.setStyleSheet("min-width: 95px; font-size: 11px;")
        self.img_size_combo.addItem("Small (200px)", 200)
        self.img_size_combo.addItem("Medium (320px)", 320)
        self.img_size_combo.addItem("Large (480px)", 480)
        self.img_size_combo.addItem("Full Width", 640)
        self.img_size_combo.setCurrentIndex(1)  # Default: Medium (320px)
        pos_layout.addWidget(self.img_size_combo)

        pos_layout.addStretch()

        paste_hint = QLabel("Ctrl+V / Right-Click to Resize")
        paste_hint.setStyleSheet("color: #D4A373; font-size: 11px; font-weight: bold;")
        pos_layout.addWidget(paste_hint)

        self.add_img_btn = QPushButton("+ Insert Image")
        self.add_img_btn.setObjectName("SecondaryButton")
        self.add_img_btn.setCursor(Qt.PointingHandCursor)
        self.add_img_btn.setStyleSheet("padding: 2px 8px; font-size: 11px;")
        self.add_img_btn.clicked.connect(self.upload_image)
        pos_layout.addWidget(self.add_img_btn)

        self.layout.addWidget(pos_bar)

        # Text Formatting Toolbar (Bold, Italic, Underline, Size, Color)
        fmt_toolbar = QFrame()
        fmt_toolbar.setObjectName("FormatToolbar")
        fmt_layout = QHBoxLayout(fmt_toolbar)
        fmt_layout.setContentsMargins(6, 2, 6, 2)
        fmt_layout.setSpacing(6)

        fmt_label = QLabel("Text Format:")
        fmt_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #D4A373;")
        fmt_layout.addWidget(fmt_label)

        self.btn_bold = QPushButton("B")
        self.btn_bold.setCheckable(True)
        self.btn_bold.setFixedSize(26, 22)
        self.btn_bold.setStyleSheet("font-weight: bold; font-size: 11px;")
        self.btn_bold.setToolTip("Bold")
        self.btn_bold.clicked.connect(self.set_bold)
        fmt_layout.addWidget(self.btn_bold)

        self.btn_italic = QPushButton("I")
        self.btn_italic.setCheckable(True)
        self.btn_italic.setFixedSize(26, 22)
        self.btn_italic.setStyleSheet("font-style: italic; font-weight: bold; font-size: 11px;")
        self.btn_italic.setToolTip("Italic")
        self.btn_italic.clicked.connect(self.set_italic)
        fmt_layout.addWidget(self.btn_italic)

        self.btn_underline = QPushButton("U")
        self.btn_underline.setCheckable(True)
        self.btn_underline.setFixedSize(26, 22)
        self.btn_underline.setStyleSheet("font-weight: bold; font-size: 11px;")
        self.btn_underline.setToolTip("Underline")
        self.btn_underline.clicked.connect(self.set_underline)
        fmt_layout.addWidget(self.btn_underline)

        font_size_label = QLabel("Size:")
        font_size_label.setStyleSheet("font-size: 11px; color: #A89F91;")
        fmt_layout.addWidget(font_size_label)

        self.size_combo = QComboBox()
        self.size_combo.setView(QListView())
        self.size_combo.setStyleSheet("min-width: 55px;")
        for size in [12, 14, 16, 18, 20, 24, 28, 32, 36]:
            self.size_combo.addItem(str(size), size)
        self.size_combo.setCurrentText("14")
        self.size_combo.currentIndexChanged.connect(self.on_size_changed)
        fmt_layout.addWidget(self.size_combo)

        color_label = QLabel("Color:")
        color_label.setStyleSheet("font-size: 11px; color: #A89F91;")
        fmt_layout.addWidget(color_label)

        self.btn_color = QPushButton("A Color")
        self.btn_color.setObjectName("SecondaryButton")
        self.btn_color.setStyleSheet("font-size: 11px; padding: 2px 8px; font-weight: bold;")
        self.btn_color.setToolTip("Choose Text Color")
        self.btn_color.clicked.connect(self.choose_text_color)
        fmt_layout.addWidget(self.btn_color)

        fmt_layout.addStretch()
        self.layout.addWidget(fmt_toolbar)

        # Single Unified Clean Warm Note Paper Text Editor (Images & Text integrated seamlessly)
        self.text_edit = NotePaperTextEdit()
        self.text_edit.setObjectName("NotePaperEdit")
        self.text_edit.setPlaceholderText("Type note text here... Insert or paste images directly inline, above, or below like Word / Teams! (Right-click image or double-click to resize)")
        self.text_edit.image_pasted.connect(self.on_image_pasted)
        self.text_edit.image_double_clicked.connect(self.open_lightbox)
        self.text_edit.document_modified.connect(self.on_document_modified)
        self.text_edit.selectionChanged.connect(self.update_format_buttons_state)

        self.layout.addWidget(self.text_edit, 1)

        # In-App Audio Player Widget
        self.audio_player = InAppAudioPlayerWidget()
        self.audio_player.recording_requested.connect(self.toggle_recording)
        self.audio_player.import_requested.connect(self.import_audio_file)
        self.audio_player.audio_deleted.connect(self.delete_audio_track)
        self.layout.addWidget(self.audio_player)

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

    def update_format_buttons_state(self):
        self.btn_bold.blockSignals(True)
        self.btn_italic.blockSignals(True)
        self.btn_underline.blockSignals(True)

        self.btn_bold.setChecked(self.text_edit.fontWeight() == QFont.Bold)
        self.btn_italic.setChecked(self.text_edit.fontItalic())
        self.btn_underline.setChecked(self.text_edit.fontUnderline())

        self.btn_bold.blockSignals(False)
        self.btn_italic.blockSignals(False)
        self.btn_underline.blockSignals(False)

    def load_note(self, note):
        self.current_note = note
        html = note.get("content_html") or note.get("content", "")
        self.text_edit.setHtml(html)
        
        pos = note.get("image_position", "inline")
        if pos == "top":
            self.radio_top.setChecked(True)
        elif pos == "bottom":
            self.radio_bottom.setChecked(True)
        else:
            self.radio_inline.setChecked(True)

        audio_files = note.get("audio_files", [])
        self.audio_player.load_audio_files(audio_files)

    def get_current_data(self):
        if not self.current_note:
            self.current_note = {}
        
        self.current_note["content"] = self.text_edit.toPlainText()
        self.current_note["content_html"] = self.text_edit.toHtml()

        if self.radio_top.isChecked():
            self.current_note["image_position"] = "top"
        elif self.radio_bottom.isChecked():
            self.current_note["image_position"] = "bottom"
        else:
            self.current_note["image_position"] = "inline"
            
        return self.current_note

    def on_image_pos_changed(self):
        if self.current_note:
            if self.radio_top.isChecked():
                self.current_note["image_position"] = "top"
            elif self.radio_bottom.isChecked():
                self.current_note["image_position"] = "bottom"
            else:
                self.current_note["image_position"] = "inline"

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
        
        # Get selected width from img_size_combo
        img_w = self.img_size_combo.currentData() or 320

        fmt = QTextImageFormat()
        fmt.setName(file_path)
        fmt.setWidth(img_w)

        if self.radio_top.isChecked():
            cursor.movePosition(QTextCursor.Start)
            cursor.insertImage(fmt)
            cursor.insertBlock()
        elif self.radio_bottom.isChecked():
            cursor.movePosition(QTextCursor.End)
            cursor.insertBlock()
            cursor.insertImage(fmt)
            cursor.insertBlock()
        else: # Inline at cursor
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

    def toggle_recording(self):
        if not self.current_note:
            QMessageBox.warning(self, "Warning", "Select or create a note before recording audio.")
            return

        if not self.audio_engine.is_recording:
            self.audio_engine.start_recording()
            self.audio_player.rec_btn.setText("Recording...")
            self.audio_player.rec_btn.setStyleSheet("background-color: #DC2626; font-weight: bold; font-size: 11px; padding: 3px 8px;")
        else:
            path, duration = self.audio_engine.stop_recording()
            self.audio_player.rec_btn.setText("+ Record Voice")
            self.audio_player.rec_btn.setStyleSheet("background-color: #B91C1C; font-weight: bold; font-size: 11px; padding: 3px 8px;")
            
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

            self.audio_player.load_audio_files(audio_files)
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

        self.audio_player.load_audio_files(audio_files)
        self.db.add_or_update_note(self.current_note)
        self.audio_files_updated.emit(self.current_note)

    def delete_audio_track(self, track_obj):
        if self.current_note and "audio_files" in self.current_note:
            target_path = track_obj.get("path") if isinstance(track_obj, dict) else track_obj
            self.current_note["audio_files"] = [
                a for a in self.current_note["audio_files"] 
                if (a.get("path") if isinstance(a, dict) else a) != target_path
            ]
            self.audio_player.load_audio_files(self.current_note["audio_files"])
            self.db.add_or_update_note(self.current_note)
            self.audio_files_updated.emit(self.current_note)
