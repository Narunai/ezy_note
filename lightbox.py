import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, 
    QFrame, QSlider, QMessageBox
)
from PySide6.QtGui import QPixmap, QKeySequence, QShortcut
from PySide6.QtCore import Qt, QSize, Signal

class ImageLightboxDialog(QDialog):
    size_selected = Signal(int)

    def __init__(self, image_path, caption="", position_tag="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Image Preview & Scale Adjuster")
        self.resize(850, 650)
        self.setStyleSheet("background-color: #161412; color: #F5EFE6;")
        self.image_path = image_path

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Header bar with file info and position tag
        header_layout = QHBoxLayout()
        filename = os.path.basename(image_path)
        title_label = QLabel(f"🖼️ [Image] {filename}")
        title_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #D4A373;")
        header_layout.addWidget(title_label)

        if position_tag:
            pos_label = QLabel(f"[{position_tag}]")
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
                font-size: 11px;
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

        # Bottom Toolbar: Quick Note Resizing & Caption
        bottom_bar = QFrame()
        bottom_bar.setStyleSheet("background-color: #201D1A; border: 1px solid #332E28; border-radius: 6px; padding: 6px 10px;")
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(6, 4, 6, 4)
        bottom_layout.setSpacing(8)

        scale_lbl = QLabel("📐 Adjust Size in Note:")
        scale_lbl.setStyleSheet("font-weight: bold; font-size: 11px; color: #D4A373;")
        bottom_layout.addWidget(scale_lbl)

        for name, width in [("Small (200px)", 200), ("Medium (320px)", 320), ("Large (480px)", 480), ("Full Width", 640)]:
            btn = QPushButton(name)
            btn.setObjectName("SecondaryButton")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("font-size: 11px; padding: 3px 8px;")
            btn.clicked.connect(lambda _, w=width: self.apply_size_and_close(w))
            bottom_layout.addWidget(btn)

        bottom_layout.addStretch()

        caption_text = caption if caption else "Embedded Note Image"
        cap_label = QLabel(f"ℹ️ {caption_text}")
        cap_label.setStyleSheet("color: #A89F91; font-size: 11px;")
        bottom_layout.addWidget(cap_label)

        layout.addWidget(bottom_bar)

        shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
        shortcut.activated.connect(self.close)

    def apply_size_and_close(self, width):
        self.size_selected.emit(width)
        self.close()

    def update_image(self):
        if not self.pixmap.isNull():
            scaled = self.pixmap.scaled(
                self.size() - QSize(40, 160),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_image()
