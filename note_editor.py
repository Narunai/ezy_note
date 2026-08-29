import os
import time
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QLineEdit,
    QPushButton, QFileDialog, QRadioButton, QFrame, QMessageBox, QScrollArea,
    QComboBox, QColorDialog
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPixmap, QIcon, QImage, QFont, QColor

from lightbox import ImageLightboxDialog
from database import MEDIA_DIR
from audio_player_widget import InAppAudioPlayerWidget

class NotePaperTextEdit(QTextEdit):
    image_pasted = Signal(str)

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


class NoteEditorWidget(QWidget):
    note_saved = Signal(dict)

    def __init__(self, db, audio_engine, parent=None):
        super().__init__(parent)
        self.db = db
        self.audio_engine = audio_engine
        self.current_note = None

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(6, 6, 6, 6)
        self.layout.setSpacing(6)

        # Image Placement & Meaning Control Banner
        pos_bar = QFrame()
        pos_bar.setObjectName("ImagePosBanner")
        pos_layout = QHBoxLayout(pos_bar)
        pos_layout.setContentsMargins(8, 2, 8, 2)
        pos_layout.setSpacing(8)

        pos_label = QLabel("Image Position:")
        pos_label.setStyleSheet("font-weight: bold; color: #D4A373; font-size: 11px;")
        pos_layout.addWidget(pos_label)

        self.radio_top = QRadioButton("Above")
        self.radio_inline = QRadioButton("Inline")
        self.radio_bottom = QRadioButton("Below")

        self.radio_top.setStyleSheet("font-size: 11px;")
        self.radio_inline.setStyleSheet("font-size: 11px;")
        self.radio_bottom.setStyleSheet("font-size: 11px;")

        self.radio_inline.setChecked(True)

        self.radio_top.toggled.connect(self.on_image_pos_changed)
        self.radio_inline.toggled.connect(self.on_image_pos_changed)
        self.radio_bottom.toggled.connect(self.on_image_pos_changed)

        pos_layout.addWidget(self.radio_top)
        pos_layout.addWidget(self.radio_inline)
        pos_layout.addWidget(self.radio_bottom)
        pos_layout.addStretch()

        paste_hint = QLabel("Ctrl+V to paste image")
        paste_hint.setStyleSheet("color: #D4A373; font-size: 11px; font-weight: bold;")
        pos_layout.addWidget(paste_hint)

        self.add_img_btn = QPushButton("+ Add Image")
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

        size_label = QLabel("Size:")
        size_label.setStyleSheet("font-size: 11px; color: #A89F91;")
        fmt_layout.addWidget(size_label)

        self.size_combo = QComboBox()
        self.size_combo.setStyleSheet("font-size: 11px; min-width: 55px;")
        for size in [12, 14, 16, 18, 20, 24, 28]:
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

        # Scrollable Note Paper Canvas Container
        self.paper_container = QWidget()
        self.paper_layout = QVBoxLayout(self.paper_container)
        self.paper_layout.setContentsMargins(0, 0, 0, 0)
        self.paper_layout.setSpacing(6)

        # Top Images Container
        self.top_images_container = QWidget()
        self.top_images_layout = QHBoxLayout(self.top_images_container)
        self.top_images_layout.setContentsMargins(0, 0, 0, 0)
        self.top_images_layout.setAlignment(Qt.AlignLeft)

        # Clean Warm Note Paper Text Editor
        self.text_edit = NotePaperTextEdit()
        self.text_edit.setObjectName("NotePaperEdit")
        self.text_edit.setPlaceholderText("Type note text here... Select text to apply Bold, Italic, Size, or Text Color!")
        self.text_edit.image_pasted.connect(self.on_image_pasted)
        self.text_edit.selectionChanged.connect(self.update_format_buttons_state)

        # Bottom Images Container
        self.bottom_images_container = QWidget()
        self.bottom_images_layout = QHBoxLayout(self.bottom_images_container)
        self.bottom_images_layout.setContentsMargins(0, 0, 0, 0)
        self.bottom_images_layout.setAlignment(Qt.AlignLeft)

        # Inline Images Container
        self.inline_images_container = QWidget()
        self.inline_images_layout = QVBoxLayout(self.inline_images_container)
        self.inline_images_layout.setContentsMargins(0, 0, 0, 0)
        self.inline_images_layout.setSpacing(6)

        self.paper_layout.addWidget(self.top_images_container)
        self.paper_layout.addWidget(self.text_edit, 1)
        self.paper_layout.addWidget(self.inline_images_container)
        self.paper_layout.addWidget(self.bottom_images_container)

        self.layout.addWidget(self.paper_container, 1)

        # In-App Audio Player Widget
        self.audio_player = InAppAudioPlayerWidget()
        self.audio_player.recording_requested.connect(self.toggle_recording)
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
        if size:
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
        self.text_edit.setHtml(note.get("content_html", note.get("content", "")))
        
        pos = note.get("image_position", "inline")
        if pos == "top":
            self.radio_top.setChecked(True)
        elif pos == "bottom":
            self.radio_bottom.setChecked(True)
        else:
            self.radio_inline.setChecked(True)

        audio_files = note.get("audio_files", [])
        self.audio_player.load_audio_files(audio_files)
        self.render_images()

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
            self.render_images()

    def upload_image(self):
        if not self.current_note:
            QMessageBox.warning(self, "Warning", "Select or create a note before adding images.")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", "Image Files (*.png *.jpg *.jpeg *.webp *.gif)"
        )
        if file_path:
            self.on_image_pasted(file_path)

    def on_image_pasted(self, file_path):
        if not self.current_note:
            return
        images = self.current_note.setdefault("images", [])
        image_obj = {
            "path": file_path,
            "caption": "Image (Ctrl+V)",
            "position_tag": f"Position #{len(images)+1}"
        }
        images.append(image_obj)
        self.render_images()
        self.db.add_or_update_note(self.current_note)

    def render_images(self):
        for l in [self.top_images_layout, self.bottom_images_layout, self.inline_images_layout]:
            for i in reversed(range(l.count())):
                widget = l.itemAt(i).widget()
                if widget:
                    widget.setParent(None)

        if not self.current_note:
            return

        raw_images = self.current_note.get("images", [])
        pos = self.current_note.get("image_position", "inline")

        images = []
        for idx, item in enumerate(raw_images):
            if isinstance(item, str):
                images.append({"path": item, "caption": "Image context", "position_tag": f"Image #{idx+1}"})
            elif isinstance(item, dict):
                images.append(item)

        if pos == "top":
            for img in images:
                self.top_images_layout.addWidget(self.create_image_card(img, "Above Text"))
        elif pos == "bottom":
            for img in images:
                self.bottom_images_layout.addWidget(self.create_image_card(img, "Below Text"))
        else: # Inline mode
            for idx, img in enumerate(images):
                pos_tag = f"Inline (Paragraph #{idx+1})"
                self.inline_images_layout.addWidget(self.create_inline_image_strip(img, pos_tag))

    def create_image_card(self, img_obj, pos_tag):
        img_path = img_obj.get("path", "")
        caption = img_obj.get("caption", "")

        thumb_card = QFrame()
        thumb_card.setObjectName("InlineImageCard")
        thumb_card.setFixedWidth(160)
        card_layout = QVBoxLayout(thumb_card)
        card_layout.setContentsMargins(4, 4, 4, 4)
        card_layout.setSpacing(4)

        img_btn = QPushButton()
        img_btn.setCursor(Qt.PointingHandCursor)
        pixmap = QPixmap(img_path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(140, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            img_btn.setIcon(QIcon(scaled))
            img_btn.setIconSize(QSize(140, 90))
        
        img_btn.setStyleSheet("border: none; background: transparent;")
        img_btn.clicked.connect(lambda _, path=img_path, cap=caption, tag=pos_tag: self.open_lightbox(path, cap, tag))
        card_layout.addWidget(img_btn)

        cap_input = QLineEdit()
        cap_input.setObjectName("CaptionInput")
        cap_input.setPlaceholderText("Caption...")
        cap_input.setText(caption)
        cap_input.textChanged.connect(lambda text, obj=img_obj: self.update_caption(obj, text))
        card_layout.addWidget(cap_input)

        del_btn = QPushButton("✕ Delete")
        del_btn.setStyleSheet("""
            QPushButton {
                background-color: #E2E8F0;
                color: #B91C1C;
                font-size: 10px;
                padding: 2px 4px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #B91C1C;
                color: #FFFFFF;
            }
        """)
        del_btn.clicked.connect(lambda _, path=img_path: self.delete_image(path))
        card_layout.addWidget(del_btn)

        return thumb_card

    def create_inline_image_strip(self, img_obj, pos_tag):
        img_path = img_obj.get("path", "")
        caption = img_obj.get("caption", "")

        strip_card = QFrame()
        strip_card.setObjectName("InlineImageCard")
        strip_layout = QHBoxLayout(strip_card)
        strip_layout.setContentsMargins(6, 4, 6, 4)
        strip_layout.setSpacing(8)

        img_btn = QPushButton()
        img_btn.setCursor(Qt.PointingHandCursor)
        pixmap = QPixmap(img_path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(100, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            img_btn.setIcon(QIcon(scaled))
            img_btn.setIconSize(QSize(100, 70))
        
        img_btn.setStyleSheet("border: none; background: transparent;")
        img_btn.clicked.connect(lambda _, path=img_path, cap=caption, tag=pos_tag: self.open_lightbox(path, cap, tag))
        strip_layout.addWidget(img_btn)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        tag_label = QLabel(f"Location: {pos_tag}")
        tag_label.setStyleSheet("color: #8B5E3C; font-weight: bold; font-size: 11px;")
        info_layout.addWidget(tag_label)

        cap_input = QLineEdit()
        cap_input.setObjectName("CaptionInput")
        cap_input.setPlaceholderText("Caption...")
        cap_input.setText(caption)
        cap_input.textChanged.connect(lambda text, obj=img_obj: self.update_caption(obj, text))
        info_layout.addWidget(cap_input)

        strip_layout.addLayout(info_layout, 1)

        del_btn = QPushButton("✕ Delete")
        del_btn.setStyleSheet("""
            QPushButton {
                background-color: #E6DFD5;
                color: #B91C1C;
                font-size: 10px;
                padding: 4px 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #B91C1C;
                color: #FFFFFF;
            }
        """)
        del_btn.clicked.connect(lambda _, path=img_path: self.delete_image(path))
        strip_layout.addWidget(del_btn)

        return strip_card

    def update_caption(self, img_obj, new_caption):
        img_obj["caption"] = new_caption

    def open_lightbox(self, image_path, caption="", position_tag=""):
        dlg = ImageLightboxDialog(image_path, caption, position_tag, self)
        dlg.exec()

    def delete_image(self, image_path):
        if self.current_note and "images" in self.current_note:
            self.current_note["images"] = [
                img for img in self.current_note["images"] 
                if (isinstance(img, str) and img != image_path) or (isinstance(img, dict) and img.get("path") != image_path)
            ]
            self.render_images()

    def toggle_recording(self):
        if not self.current_note:
            QMessageBox.warning(self, "Warning", "Select or create a note before recording audio.")
            return

        if not self.audio_engine.is_recording:
            self.audio_engine.start_recording()
            self.audio_player.rec_btn.setText("Recording...")
            self.audio_player.rec_btn.setStyleSheet("background-color: #DC2626; font-weight: bold; font-size: 11px;")
        else:
            path, duration = self.audio_engine.stop_recording()
            self.audio_player.rec_btn.setText("+ Record Voice")
            self.audio_player.rec_btn.setStyleSheet("background-color: #B91C1C; font-weight: bold; font-size: 11px;")
            
            audio_files = self.current_note.setdefault("audio_files", [])
            new_clip = {
                "path": path,
                "duration": duration,
                "name": f"Voice #{len(audio_files)+1}"
            }
            audio_files.append(new_clip)

            transcript = self.audio_engine.transcribe_audio(path)
            summary = self.audio_engine.generate_summary(transcript)
            self.current_note["transcript"] = (self.current_note.get("transcript", "") + "\n\n" + transcript).strip()
            self.current_note["summary"] = summary

            self.audio_player.load_audio_files(audio_files)
            self.db.add_or_update_note(self.current_note)

    def delete_audio_track(self, track_obj):
        if self.current_note and "audio_files" in self.current_note:
            self.current_note["audio_files"] = [
                a for a in self.current_note["audio_files"] if a.get("path") != track_obj.get("path")
            ]
            self.audio_player.load_audio_files(self.current_note["audio_files"])
            self.db.add_or_update_note(self.current_note)
