from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QPoint

class CustomTitleBar(QWidget):
    def __init__(self, parent_window):
        super().__init__(parent_window)
        self.window = parent_window
        self.setObjectName("CustomTitleBar")
        self.setFixedHeight(32)

        self.drag_position = QPoint()
        self.is_dragging = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 4, 0)
        layout.setSpacing(6)

        # Title Label - Monochrome Minimalist
        self.title_label = QLabel("NoteGod  —  Minimalist Note & Voice AI")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 11px; color: #D4A373;")
        layout.addWidget(self.title_label)

        layout.addStretch()

        # Window Control Buttons
        self.min_btn = QPushButton("—")
        self.min_btn.setObjectName("TitleBarBtn")
        self.min_btn.setFixedSize(28, 22)
        self.min_btn.setToolTip("Minimize")
        self.min_btn.clicked.connect(self.window.showMinimized)
        layout.addWidget(self.min_btn)

        self.max_btn = QPushButton("☐")
        self.max_btn.setObjectName("TitleBarBtn")
        self.max_btn.setFixedSize(28, 22)
        self.max_btn.setToolTip("Maximize / Restore")
        self.max_btn.clicked.connect(self.toggle_maximized)
        layout.addWidget(self.max_btn)

        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("TitleBarCloseBtn")
        self.close_btn.setFixedSize(28, 22)
        self.close_btn.setToolTip("Close")
        self.close_btn.clicked.connect(self.window.close)
        layout.addWidget(self.close_btn)

    def toggle_maximized(self):
        if self.window.isMaximized():
            self.window.showNormal()
            self.max_btn.setText("☐")
        else:
            self.window.showMaximized()
            self.max_btn.setText("❐")

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.toggle_maximized()
