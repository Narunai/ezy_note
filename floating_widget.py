from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt, Signal, QPoint, QSize
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QCursor, QIcon

class FloatingNoteWidget(QWidget):
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | 
            Qt.FramelessWindowHint | 
            Qt.Tool | 
            Qt.SubWindow
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(70, 70)

        # Position widget initially on right side of screen
        self.drag_position = QPoint()
        self.is_dragging = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)

        # Floating Card Container
        self.card = QLabel("📝", self)
        self.card.setAlignment(Qt.AlignCenter)
        self.card.setStyleSheet("""
            QLabel {
                background-color: #6366F1;
                border: 3px solid #818CF8;
                border-radius: 35px;
                font-size: 30px;
            }
            QLabel:hover {
                background-color: #4F46E5;
                border: 3px solid #A5B4FC;
            }
        """)
        self.card.setFixedSize(70, 70)
        self.card.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.card)

        # Badge count label
        self.badge = QLabel("1", self)
        self.badge.setStyleSheet("""
            QLabel {
                background-color: #EF4444;
                color: #FFFFFF;
                border-radius: 10px;
                font-size: 11px;
                font-weight: bold;
                padding: 2px 6px;
            }
        """)
        self.badge.move(46, 4)
        self.badge.hide()

    def set_badge_count(self, count):
        if count > 0:
            self.badge.setText(str(count))
            self.badge.show()
        else:
            self.badge.hide()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.is_dragging and event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.is_dragging:
                # If mouse moved only slightly, consider it a click!
                move_dist = (event.globalPosition().toPoint() - self.frameGeometry().topLeft() - self.drag_position).manhattanLength()
                if move_dist < 5:
                    self.clicked.emit()
            self.is_dragging = False
            event.accept()
