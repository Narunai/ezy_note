from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QCursor

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
        
        # Compact, sleek minimalist dimensions (44x44 px)
        self.widget_size = 44
        self.resize(self.widget_size, self.widget_size)

        self.drag_position = QPoint()
        self.is_dragging = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)

        # Minimalist Warm Sepia Floating Button
        self.card = QLabel("📝", self)
        self.card.setAlignment(Qt.AlignCenter)
        self.card.setStyleSheet("""
            QLabel {
                background-color: #26221E;
                color: #F5EFE6;
                border: 1.5px solid #4A3E34;
                border-radius: 22px;
                font-size: 18px;
            }
            QLabel:hover {
                background-color: #332D27;
                border: 1.5px solid #D4A373;
                color: #FFFFFF;
            }
        """)
        self.card.setFixedSize(self.widget_size, self.widget_size)
        self.card.setCursor(Qt.PointingHandCursor)
        self.card.setToolTip("Click to toggle NoteGod | Drag to move")
        layout.addWidget(self.card)

        # Minimal badge count label
        self.badge = QLabel("1", self)
        self.badge.setStyleSheet("""
            QLabel {
                background-color: #B91C1C;
                color: #FFFFFF;
                border-radius: 7px;
                font-size: 9px;
                font-weight: bold;
                padding: 1px 4px;
                min-width: 14px;
                max-height: 14px;
            }
        """)
        self.badge.setAlignment(Qt.AlignCenter)
        self.badge.move(self.widget_size - 16, 2)
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
                move_dist = (event.globalPosition().toPoint() - self.frameGeometry().topLeft() - self.drag_position).manhattanLength()
                if move_dist < 5:
                    self.clicked.emit()
            self.is_dragging = False
            event.accept()
