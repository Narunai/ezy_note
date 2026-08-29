# NoteGod GitHub/Obsidian Minimalist Warm Sepia Palette

QSS_STYLE = """
QMainWindow, QDialog {
    background-color: #161412;
    color: #F5EFE6;
    font-family: 'Segoe UI', 'Outfit', 'Inter', sans-serif;
}

QWidget {
    font-family: 'Segoe UI', 'Outfit', 'Inter', sans-serif;
    color: #F5EFE6;
}

/* Custom Minimalist TitleBar */
#CustomTitleBar {
    background-color: #161412;
    border-bottom: 1px solid #332E28;
}

#TitleBarBtn {
    background-color: transparent;
    color: #A89F91;
    border: none;
    border-radius: 4px;
    font-size: 11px;
    font-weight: bold;
}
#TitleBarBtn:hover {
    background-color: #332E28;
    color: #F5EFE6;
}

#TitleBarCloseBtn {
    background-color: transparent;
    color: #A89F91;
    border: none;
    border-radius: 4px;
    font-size: 11px;
    font-weight: bold;
}
#TitleBarCloseBtn:hover {
    background-color: #B91C1C;
    color: #FFFFFF;
}

/* Sidebar styling - GitHub Dark / Minimal Warm */
#SidebarWidget {
    background-color: #201D1A;
    border-right: 1px solid #332E28;
}

#SidebarHeader {
    background-color: #161412;
    border-bottom: 1px solid #332E28;
    padding: 6px 8px;
}

#SidebarTitle {
    font-size: 13px;
    font-weight: bold;
    color: #D4A373;
}

#SearchBox {
    background-color: #161412;
    border: 1px solid #332E28;
    border-radius: 6px;
    padding: 4px 8px;
    color: #F5EFE6;
    font-size: 12px;
}
#SearchBox:focus {
    border: 1px solid #D4A373;
}

/* Header bar - Minimal */
#EditorHeader {
    background-color: #201D1A;
    border-bottom: 1px solid #332E28;
    padding: 4px 8px;
    max-height: 42px;
}

#TitleInput {
    background: transparent;
    border: none;
    font-size: 16px;
    font-weight: bold;
    color: #F5EFE6;
    padding: 2px 4px;
}
#TitleInput:focus {
    border-bottom: 2px solid #D4A373;
}

/* Format Toolbar */
#FormatToolbar {
    background-color: #201D1A;
    border: 1px solid #332E28;
    border-radius: 6px;
    padding: 2px 6px;
}

/* Minimal Tabs */
QTabWidget::pane {
    border: 1px solid #332E28;
    background-color: #161412;
    border-radius: 6px;
}

QTabBar::tab {
    background-color: #201D1A;
    color: #A89F91;
    padding: 5px 14px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #8B5E3C;
    color: #FFFFFF;
}

QTabBar::tab:hover:!selected {
    background-color: #332E28;
    color: #F5EFE6;
}

/* Crisp Warm Note Paper Canvas */
QTextEdit#NotePaperEdit {
    background-color: #FAF8F5;
    color: #1C1917;
    border: 1px solid #E6DFD5;
    border-radius: 8px;
    padding: 16px;
    font-size: 14px;
    line-height: 1.6;
    selection-background-color: #E6C5A8;
    selection-color: #1C1917;
}
QTextEdit#NotePaperEdit:focus {
    border: 1.5px solid #D4A373;
}

/* High Contrast Readable Transcript Boxes */
QTextEdit#TranscriptTextEdit {
    background-color: #FAF8F5;
    color: #1C1917;
    border: 1px solid #E6DFD5;
    border-radius: 6px;
    padding: 12px;
    font-size: 13px;
    line-height: 1.5;
    selection-background-color: #E6C5A8;
    selection-color: #1C1917;
}

/* Minimal Inline Image Card */
#InlineImageCard {
    background-color: #F5EFE6;
    border: 1px solid #E6DFD5;
    border-radius: 8px;
    padding: 6px;
    margin: 4px 0px;
}

#CaptionInput {
    background-color: #FFFFFF;
    border: 1px solid #D8CFC4;
    border-radius: 4px;
    padding: 4px 6px;
    color: #1C1917;
    font-size: 11px;
}
#CaptionInput:focus {
    border: 1px solid #D4A373;
}

/* Buttons */
QPushButton {
    background-color: #8B5E3C;
    color: #FFFFFF;
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 12px;
    font-weight: 600;
    border: none;
}
QPushButton:hover {
    background-color: #724A2D;
}
QPushButton:pressed {
    background-color: #593922;
}

QPushButton#DangerButton {
    background-color: #B91C1C;
}
QPushButton#DangerButton:hover {
    background-color: #991B1B;
}

QPushButton#SecondaryButton {
    background-color: #201D1A;
    color: #F5EFE6;
    border: 1px solid #332E28;
}
QPushButton#SecondaryButton:hover {
    background-color: #332E28;
}

/* Banners */
#ImagePosBanner {
    background-color: #201D1A;
    border: 1px solid #332E28;
    border-radius: 6px;
    padding: 2px 6px;
    max-height: 34px;
}

#AudioPlayerWidget {
    background-color: #201D1A;
    border: 1px solid #332E28;
    border-radius: 6px;
    padding: 4px 8px;
}

/* Slim Scrollbars */
QScrollBar:vertical {
    background: #161412;
    width: 6px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #332E28;
    min-height: 16px;
    border-radius: 3px;
}
QScrollBar::handle:vertical:hover {
    background: #D4A373;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""
