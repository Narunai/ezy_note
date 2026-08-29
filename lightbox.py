import os
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtGui import QPixmap, QKeySequence, QShortcut
from PySide6.QtCore import Qt, QSize

class ImageLightboxDialog(QDialog):
    def __init__(self, image_path, caption="", position_tag="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Image Lightbox & Context")
        self.resize(850, 650)
        self.setStyleSheet("background-color: #161412; color: #F5EFE6;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Header bar with file info and position tag
        header_layout = QHBoxLayout()
        filename = os.path.basename(image_path)
        title_label = QLabel(f"[Image] {filename}")
        title_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #D4A373;")
        header_layout.addWidget(title_label)

        if position_tag:
            pos_label = QLabel(f"[Location: {position_tag}]")
            pos_label.setStyleSheet("background-color: #201D1A; color: #10B981; padding: 2px 8px; border-radius: 4px; font-size: 11px;")
            header_layout.addWidget(pos_label)

        header_layout.addStretch()

        close_btn = QPushButton("✕ Close (Esc)")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #332E28;
                color: #FFFFFF;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #B91C1C;
            }
        """)
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)
        layout.addLayout(header_layout)

        # Image display container
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.pixmap = QPixmap(image_path)

        if not self.pixmap.isNull():
            self.update_image()
        else:
            self.image_label.setText("Cannot load image")
            self.image_label.setStyleSheet("color: #B91C1C; font-size: 14px;")

        layout.addWidget(self.image_label, 1)

        # Caption banner
        caption_text = caption if caption else "No additional caption provided"
        caption_box = QLabel(f"[Caption]: {caption_text}")
        caption_box.setStyleSheet("""
            QLabel {
                background-color: #201D1A;
                border: 1px solid #332E28;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 12px;
                color: #F5EFE6;
            }
        """)
        layout.addWidget(caption_box)

        shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
        shortcut.activated.connect(self.close)

    def update_image(self):
        if not self.pixmap.isNull():
            scaled = self.pixmap.scaled(
                self.size() - QSize(40, 140),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_image()
