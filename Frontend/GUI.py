from PyQt5.QtWidgets import (QApplication, QMainWindow, QTextEdit, QStackedWidget, 
                             QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, 
                             QLabel, QSizePolicy, QGraphicsDropShadowEffect)
from PyQt5.QtGui import QIcon, QColor, QTextCharFormat, QFont, QPixmap, QTextBlockFormat, QPainter, QPen, QCursor, QMovie
from PyQt5.QtCore import Qt, QTimer, QPoint, QRect, QPropertyAnimation, QEasingCurve, QSize
from dotenv import dotenv_values
import sys
import os
import ctypes
from ctypes import wintypes
import win32gui
import win32process
import psutil
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module = "pygame")

env_vars = dotenv_values('.env')
AssistantName = env_vars.get('AssistantName')
current_dir = os.getcwd()
old_chat_message = ""
TempDirPath = rf"{current_dir}/Frontend/Files"
GraphicsDirPath = r"C:\Users\as\Desktop\SARA\Frontend\Graphics"

SNAP_MARGIN = 15
SNAP_FILE = rf"{TempDirPath}/snap.data"
MAXIMIZE_SIGNAL = rf"{TempDirPath}/maximize.signal"
SNAPPED_APPS_FILE = rf"{TempDirPath}/snapped_apps.data"

def QueryModifier(Query):
    new_query = Query.lower().strip()
    query_words = new_query.split()
    question_words = ['how', 'what', 'who', 'where', 'when', 'why', 'which', 'whose', 'whom', 'can you', "what's", "where's", "how's"]
    if any(word+" " in new_query for word in question_words):
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1]+'?'
        else:
            new_query+='?'
    else:
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1]+'.'
        else:
            new_query+='.'
    return new_query.capitalize()

def SetMicrophoneStatus(Command):
    with open(rf'{TempDirPath}/Mic.data', 'w', encoding='utf-8') as file:
        file.write(Command)

def GetMicrophoneStatus():
    with open(rf'{TempDirPath}/Mic.data', 'r', encoding='utf-8') as file:
        Status = file.read()
    return Status

def SetAssistantStatus(Status):
    with open(rf'{TempDirPath}/Status.data', 'w', encoding='utf-8') as file:
        file.write(Status)

def GetAssistantStatus():
    with open(rf'{TempDirPath}/Status.data', 'r', encoding='utf-8') as file:
        Status = file.read()
    return Status

def MicButtonInitiated():
    SetMicrophoneStatus('False')

def SignalExit():
    with open(rf"{TempDirPath}/exit.signal", "w") as f:
        f.write("EXIT")

def MicButtonClosed():
    SetMicrophoneStatus('True')

def GraphicsDirectoryPath(FileName):
    Path = rf'{GraphicsDirPath}/{FileName}'
    return Path

def ShowTextToScreen(Text):
    with open(rf'{TempDirPath}/Responses.data', 'w', encoding='utf-8') as file:
        file.write(Text)

# 🆕 Helper functions for tracking snapped apps
def get_snapped_apps():
    if not os.path.exists(SNAPPED_APPS_FILE):
        return []
    try:
        with open(SNAPPED_APPS_FILE, 'r') as f:
            data = f.read().strip()
            return data.split(',') if data else []
    except:
        return []

def remove_snapped_app(app_identifier):
    snapped = get_snapped_apps()
    if app_identifier in snapped:
        snapped.remove(app_identifier)
    with open(SNAPPED_APPS_FILE, 'w') as f:
        f.write(','.join(snapped))

def clear_snapped_apps():
    with open(SNAPPED_APPS_FILE, 'w') as f:
        f.write('')

class ModernButton(QPushButton):
    """Modern styled button with hover effects"""
    def __init__(self, text="", icon=None, parent=None):
        super().__init__(text, parent)
        if icon:
            self.setIcon(icon)
        self.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
                border: 2px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
                border: 2px solid rgba(255, 255, 255, 0.4);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)

class MicButton(QPushButton):
    """Animated microphone button"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(80, 80)
        self.is_active = False
        self.updateIcon()
        self.setStyleSheet("""
            QPushButton {
                background-color: rgba(30, 144, 255, 0.8);
                border: 3px solid rgba(255, 255, 255, 0.3);
                border-radius: 40px;
            }
            QPushButton:hover {
                background-color: rgba(30, 144, 255, 1);
                border: 3px solid rgba(255, 255, 255, 0.5);
            }
            QPushButton:pressed {
                background-color: rgba(20, 120, 220, 1);
            }
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(30, 144, 255, 180))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)
        
    def updateIcon(self):
        icon_path = GraphicsDirectoryPath('Mic_on.png' if not self.is_active else 'Mic_off.png')
        pixmap = QPixmap(icon_path).scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setIcon(QIcon(pixmap))
        self.setIconSize(pixmap.size())
        
    def toggle(self):
        self.is_active = not self.is_active
        self.updateIcon()
        if self.is_active:
            self.setStyleSheet("""
                QPushButton {
                    background-color: rgba(220, 53, 69, 0.8);
                    border: 3px solid rgba(255, 255, 255, 0.3);
                    border-radius: 40px;
                }
                QPushButton:hover {
                    background-color: rgba(220, 53, 69, 1);
                    border: 3px solid rgba(255, 255, 255, 0.5);
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: rgba(30, 144, 255, 0.8);
                    border: 3px solid rgba(255, 255, 255, 0.3);
                    border-radius: 40px;
                }
                QPushButton:hover {
                    background-color: rgba(30, 144, 255, 1);
                    border: 3px solid rgba(255, 255, 255, 0.5);
                }
            """)

class ChatSession(QWidget):
    def __init__(self):
        super(ChatSession, self).__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        self.chat_text_edit = QTextEdit()
        self.chat_text_edit.setReadOnly(True)
        self.chat_text_edit.setFrameStyle(QFrame.NoFrame)
        self.chat_text_edit.setStyleSheet("""
            QTextEdit {
                background-color: rgba(255, 255, 255, 0.05);
                border: 2px solid rgba(255, 255, 255, 0.1);
                border-radius: 15px;
                padding: 15px;
                color: white;
            }
        """)
        layout.addWidget(self.chat_text_edit)
        
        self.png_label = QLabel()
        self.movie = QMovie(GraphicsDirectoryPath('Jarvis.gif'))
        self.png_label.setMovie(self.movie)
        self.png_label.setAlignment(Qt.AlignCenter)
        self.png_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.png_label.setScaledContents(False)
        self.movie.start()
        layout.addWidget(self.png_label)
        
        self.label = QLabel("")
        self.label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.7);
            font-size: 14px;
            padding: 10px;
        """)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
        
        font = QFont("Segoe UI", 11)
        self.chat_text_edit.setFont(font)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.loadMessages)
        self.timer.timeout.connect(self.SpeechRecogText)
        self.timer.start(50)
        
        self.setStyleSheet("""
            QScrollBar:vertical {
                border: none;
                background: rgba(255, 255, 255, 0.05);
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.3);
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.5);
            }
        """)

    def resizeEvent(self, event):
        if self.movie:
            size = int(min(self.width(), self.height()) * 0.35)
            self.movie.setScaledSize(QSize(size, size))
        super().resizeEvent(event)

    def loadMessages(self):
        global old_chat_message
        try:
            with open(rf'{TempDirPath}/Responses.data', 'r', encoding='utf-8') as file:
                messages = file.read()
                if messages and len(messages) > 1 and str(old_chat_message) != str(messages):
                    self.addMessage(message=messages, color='White')
                    old_chat_message = messages
        except:
            pass

    def SpeechRecogText(self):
        try:
            with open(rf'{TempDirPath}/Status.data', 'r', encoding='utf-8') as file:
                messages = file.read()
                self.label.setText(messages)
        except:
            pass

    def addMessage(self, message, color):
        cursor = self.chat_text_edit.textCursor()
        format = QTextCharFormat()
        formatm = QTextBlockFormat()
        formatm.setTopMargin(10)
        formatm.setLeftMargin(10)
        format.setForeground(QColor(color))
        cursor.setCharFormat(format)
        cursor.setBlockFormat(formatm)
        cursor.insertText(message + "\n")
        self.chat_text_edit.setTextCursor(cursor)

    def closeEvent(self, event):
        self.timer.stop()
        if self.movie:
            self.movie.stop()
        event.accept()

class InitialScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)
        
        self.png_label = QLabel()
        self.movie = QMovie(GraphicsDirectoryPath('Jarvis.gif'))
        self.png_label.setMovie(self.movie)
        self.png_label.setAlignment(Qt.AlignCenter)
        self.png_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.png_label.setScaledContents(False)
        self.movie.start()
        layout.addWidget(self.png_label)
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("""
            color: white;
            font-size: 16px;
            font-weight: 500;
            padding: 10px;
        """)
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        self.mic_button = MicButton()
        self.mic_button.clicked.connect(self.toggle_mic)
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.addStretch()
        button_layout.addWidget(self.mic_button)
        button_layout.addStretch()
        layout.addWidget(button_container)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_status)
        self.timer.timeout.connect(self.update_mic_icon)
        self.timer.start(100)

    def resizeEvent(self, event):
        if self.movie and self.width() > 50 and self.height() > 50:
            size = int(min(self.width(), self.height()) * 0.45)
            self.movie.setScaledSize(QSize(size, size))
        super().resizeEvent(event)

    def update_status(self):
        try:
            with open(rf'{TempDirPath}/Status.data', 'r', encoding='utf-8') as file:
                status = file.read()
                self.status_label.setText(status)
        except:
            pass

    def update_mic_icon(self):
        status = GetMicrophoneStatus()
        if status == 'True' and not self.mic_button.is_active:
            self.mic_button.is_active = True
            self.mic_button.updateIcon()
        elif status == 'False' and self.mic_button.is_active:
            self.mic_button.is_active = False
            self.mic_button.updateIcon()

    def toggle_mic(self):
        pass

    def closeEvent(self, event):
        self.timer.stop()
        if self.movie:
            self.movie.stop()
        event.accept()

class MessageScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        chat_session = ChatSession()
        layout.addWidget(chat_session)

class CustomTopBar(QWidget):
    def __init__(self, parent, stacked_widget):
        super().__init__(parent)
        self.stacked_widget = stacked_widget
        self.offset = None
        self.dragging_from_maximized = False
        self.initUI()

    def initUI(self):
        self.setFixedHeight(60)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        
        title_label = QLabel(f"  {str(AssistantName).upper()} AI")
        title_label.setStyleSheet("""
            color: white;
            font-size: 18px;
            font-weight: bold;
            letter-spacing: 1px;
        """)
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        home_button = ModernButton(" Home", QIcon(GraphicsDirectoryPath('Home.png')))
        home_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        layout.addWidget(home_button)
        
        chat_button = ModernButton(" Chat", QIcon(GraphicsDirectoryPath('Chats.png')))
        chat_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        layout.addWidget(chat_button)
        
        layout.addStretch()
        
        minimize_button = self.create_control_button(GraphicsDirectoryPath('Minimize2.png'))
        minimize_button.clicked.connect(self.minimizeWindow)
        layout.addWidget(minimize_button)
        
        self.maximize_button = self.create_control_button(GraphicsDirectoryPath('Maximize.png'))
        self.maximize_button.clicked.connect(self.maximizeWindow)
        self.maximize_icon = QIcon(GraphicsDirectoryPath('Maximize.png'))
        self.restore_icon = QIcon(GraphicsDirectoryPath('Minimize.png'))
        layout.addWidget(self.maximize_button)
        
        close_button = self.create_control_button(GraphicsDirectoryPath('Close.png'))
        close_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(254, 254, 254, 1);
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: rgba(220, 53, 69, 1);
            }
        """)
        close_button.clicked.connect(self.CloseWindow)
        layout.addWidget(close_button)
        
    def create_control_button(self, icon_path):
        button = QPushButton()
        button.setIcon(QIcon(icon_path))
        button.setFixedSize(40, 40)
        button.setStyleSheet("""
            QPushButton {
                background-color: rgba(254, 254, 254, 1);
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.8);
            }
        """)
        return button

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        from PyQt5.QtGui import QLinearGradient
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0, QColor(20, 20, 30))
        gradient.setColorAt(1, QColor(30, 30, 50))
        painter.fillRect(self.rect(), gradient)
        
        painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
        painter.drawLine(0, self.height()-1, self.width(), self.height()-1)

    def minimizeWindow(self):
        self.window().showMinimized()
    
    def maximizeWindow(self):
        if self.window().isMaximized():
            self.window().showNormal()
            self.maximize_button.setIcon(self.maximize_icon)
        else:
            self.window().showMaximized()
            self.maximize_button.setIcon(self.restore_icon)

    def CloseWindow(self):
        from Backend.TextToSpeech import StopTTS
        StopTTS()
        SignalExit()
        QApplication.quit()


    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            window = self.window()

            if window.isMaximized():
                self.dragging_from_maximized = True
            else:
                self.dragging_from_maximized = False
                self.offset = event.globalPos() - window.frameGeometry().topLeft()

            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() != Qt.LeftButton:
            return

        window = self.window()
        screen = QApplication.primaryScreen().availableGeometry()
        cursor_pos = event.globalPos()

        if self.dragging_from_maximized:
            window.showNormal()

            restored_width = window.width()
            restored_height = window.height()

            x_ratio = cursor_pos.x() / screen.width()
            new_x = int(screen.width() * x_ratio - restored_width / 2)

            window.move(new_x, cursor_pos.y() - 20)

            self.offset = cursor_pos - window.frameGeometry().topLeft()
            self.dragging_from_maximized = False
            return

        if cursor_pos.x() <= screen.x() + SNAP_MARGIN:
            window.setGeometry(
                screen.x(),
                screen.y(),
                screen.width() // 2,
                screen.height()
            )
            return

        if cursor_pos.x() >= screen.x() + screen.width() - SNAP_MARGIN:
            window.setGeometry(
                screen.x() + screen.width() // 2,
                screen.y(),
                screen.width() // 2,
                screen.height()
            )
            return

        if cursor_pos.y() <= screen.y() + SNAP_MARGIN:
            window.showMaximized()
            return

        if self.offset and not window.isMaximized():
            window.move(cursor_pos - self.offset)

    def mouseReleaseEvent(self, event):
        self.offset = None
        self.dragging_from_maximized = False
        event.accept()

    def mouseDoubleClickEvent(self, event):
        self.maximizeWindow()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(650, 500)
        
        # 🆕 Timers for snap and window monitoring
        self.snap_timer = QTimer(self)
        self.snap_timer.timeout.connect(self.check_snap_request)
        self.snap_timer.start(200)
        
        self.monitor_timer = QTimer(self)
        self.monitor_timer.timeout.connect(self.monitor_snapped_windows)
        self.monitor_timer.start(500)
        
        self.maximize_timer = QTimer(self)
        self.maximize_timer.timeout.connect(self.check_maximize_signal)
        self.maximize_timer.start(200)
        
        self._resizing = False
        self._resize_dir = None
        self._start_pos = QPoint()
        self._start_geom = QRect()
        
        self.initUI()

    def snap_left(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.setGeometry(
            screen.x(),
            screen.y(),
            screen.width() // 2,
            screen.height()
        )

    def check_snap_request(self):
        if not os.path.exists(SNAP_FILE):
            return
        with open(SNAP_FILE, 'r') as f:
            cmd = f.read().strip()
        if cmd == "LEFT":
            self.snap_left()
        os.remove(SNAP_FILE)

    # 🆕 Check for maximize signal
    def check_maximize_signal(self):
        if not os.path.exists(MAXIMIZE_SIGNAL):
            return
        try:
            with open(MAXIMIZE_SIGNAL, 'r') as f:
                cmd = f.read().strip()
            if cmd == "MAXIMIZE":
                self.showMaximized()
                print("GUI maximized after app close")
            os.remove(MAXIMIZE_SIGNAL)
        except:
            pass

    # 🆕 Monitor snapped windows for manual closure
    def monitor_snapped_windows(self):
        snapped_apps = get_snapped_apps()
        if not snapped_apps:
            return
        
        # Get all running process names
        running_processes = {}
        for proc in psutil.process_iter(['name', 'pid']):
            if proc.info['name']:
                proc_name = proc.info['name'].lower().replace('.exe', '')
                running_processes[proc_name] = proc.info['pid']
        
        # Check if any snapped app is no longer running
        apps_to_remove = []
        for app in snapped_apps:
            app_found = False
            app_lower = app.lower()
            
            # Check exact match first
            if app_lower in running_processes:
                app_found = True
            else:
                # Check partial matches (more flexible)
                for proc_name in running_processes.keys():
                    # Check if app name is in process name or vice versa
                    if app_lower in proc_name or proc_name in app_lower:
                        app_found = True
                        break
                    
                    # Check word-by-word matching
                    app_words = set(app_lower.split())
                    proc_words = set(proc_name.split())
                    if app_words & proc_words:  # If any word matches
                        app_found = True
                        break
            
            if not app_found:
                apps_to_remove.append(app)
                print(f"Detected manual closure of: {app}")
        
        # Remove closed apps and maximize if none remain
        for app in apps_to_remove:
            remove_snapped_app(app)
        
        if apps_to_remove:
            remaining = get_snapped_apps()
            print(f"Remaining snapped apps: {remaining}")
            if not remaining:
                print("All snapped apps closed, maximizing GUI")
                self.showMaximized()

    def initUI(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.setWindowTitle(f"{AssistantName} AI Assistant")
        self.setWindowIcon(QIcon(GraphicsDirectoryPath('app_icon.ico')))
        
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background: #0F0F1E;
                border-radius: 15px;
            }
        """)
        
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        stacked_widget = QStackedWidget()
        stacked_widget.addWidget(InitialScreen(self))
        stacked_widget.addWidget(MessageScreen(self))
        
        top_bar = CustomTopBar(self, stacked_widget)
        
        main_layout.addWidget(top_bar)
        main_layout.addWidget(stacked_widget)
        
        self.setCentralWidget(container)
        
        self.setGeometry(
            screen.x() + screen.width() // 4,
            screen.y() + screen.height() // 6,
            screen.width() // 2,
            screen.height() * 2 // 3
        )
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 10)
        container.setGraphicsEffect(shadow)

    def nativeEvent(self, eventType, message):
        if eventType != "windows_generic_MSG":
            return False, 0

        msg = wintypes.MSG.from_address(int(message))
        WM_NCHITTEST = 0x0084

        if msg.message == WM_NCHITTEST:
            x = ctypes.c_short(msg.lParam & 0xffff).value
            y = ctypes.c_short((msg.lParam >> 16) & 0xffff).value
            pos = self.mapFromGlobal(QPoint(x, y))

            m = 10
            w, h = self.width(), self.height()

            if pos.x() <= m and pos.y() <= m:
                self.setCursor(QCursor(Qt.SizeFDiagCursor))
                return True, 13
            if pos.x() >= w - m and pos.y() <= m:
                self.setCursor(QCursor(Qt.SizeBDiagCursor))
                return True, 14
            if pos.x() <= m and pos.y() >= h - m:
                self.setCursor(QCursor(Qt.SizeBDiagCursor))
                return True, 16
            if pos.x() >= w - m and pos.y() >= h - m:
                self.setCursor(QCursor(Qt.SizeFDiagCursor))
                return True, 17

            if pos.y() <= m:
                self.setCursor(QCursor(Qt.SizeVerCursor))
                return True, 12
            if pos.y() >= h - m:
                self.setCursor(QCursor(Qt.SizeVerCursor))
                return True, 15
            if pos.x() <= m:
                self.setCursor(QCursor(Qt.SizeHorCursor))
                return True, 10
            if pos.x() >= w - m:
                self.setCursor(QCursor(Qt.SizeHorCursor))
                return True, 11

            self.setCursor(QCursor(Qt.ArrowCursor))
            return False, 0

        return False, 0

    def leaveEvent(self, event):
        self.setCursor(Qt.ArrowCursor)
        super().leaveEvent(event)

    def closeEvent(self, event):
        self.snap_timer.stop()
        self.monitor_timer.stop()
        self.maximize_timer.stop()
        clear_snapped_apps()
        SignalExit()
        event.accept()



def GraphicalUserInterface():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(GraphicsDirectoryPath('app_icon.ico')))
    SetMicrophoneStatus("False")
    window = MainWindow()
    window.show()
    exit_code = app.exec_()
    sys.exit(exit_code)

# if __name__ == '__main__':
#     GraphicalUserInterface()
