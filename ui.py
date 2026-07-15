import sys
import webbrowser
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextBrowser, QApplication)
from PyQt6.QtCore import Qt, QPoint, QTimer
from PyQt6.QtGui import QColor, QPalette, QGuiApplication

class FloatingPanel(QWidget):
    def __init__(self):
        super().__init__()
        
        # Window settings
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.resize(400, 500)
        
        # Position on the right side of the screen
        screen = QGuiApplication.primaryScreen().geometry()
        self.move(screen.width() - self.width() - 20, 50)

        # Style
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border-radius: 10px;
                border: 1px solid #45475a;
                font-family: "Segoe UI", sans-serif;
            }
            QLabel#Title {
                font-size: 16px;
                font-weight: bold;
                color: #89b4fa;
            }
            QPushButton {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 5px;
                padding: 5px 10px;
                color: #cdd6f4;
            }
            QPushButton:hover {
                background-color: #45475a;
            }
            QPushButton:pressed {
                background-color: #585b70;
            }
            QTextBrowser {
                background-color: #1e1e2e;
                border: none;
                font-size: 14px;
            }
        """)

        # Layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Header (Drag handle)
        header_layout = QHBoxLayout()
        self.title_label = QLabel("Educator's Assistant")
        self.title_label.setObjectName("Title")
        
        # Buttons
        self.btn_pin = QPushButton("📌 Pin")
        self.btn_pin.setCheckable(True)
        self.btn_hide = QPushButton("✖ Hide")
        
        self.btn_pin.clicked.connect(self.toggle_pin)
        self.btn_hide.clicked.connect(self.hide_panel)

        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_pin)
        header_layout.addWidget(self.btn_hide)
        
        # Content
        self.content_browser = QTextBrowser()
        self.content_browser.setOpenExternalLinks(False)
        self.content_browser.anchorClicked.connect(self.open_link)
        
        # Bottom controls
        self.bottom_layout = QHBoxLayout()
        self.btn_copy = QPushButton("📋 Copy Summary")
        self.btn_copy.clicked.connect(self.copy_summary)
        
        # Recording UI elements
        self.btn_cancel_rec = QPushButton("❌ Cancel Rec")
        self.btn_stop_rec = QPushButton("🛑 Stop Rec")
        self.btn_cancel_rec.setVisible(False)
        self.btn_stop_rec.setVisible(False)
        
        self.bottom_layout.addWidget(self.btn_copy)
        self.bottom_layout.addWidget(self.btn_cancel_rec)
        self.bottom_layout.addWidget(self.btn_stop_rec)
        self.bottom_layout.addStretch()

        # Add to main layout
        main_layout.addLayout(header_layout)
        main_layout.addWidget(self.content_browser)
        main_layout.addLayout(self.bottom_layout)
        
        # Dragging variables
        self.old_pos = None
        self.pinned = False
        
        self.summary_text = ""
        self.resources = []
        
        # Animation timer for micro-animation (e.g. listening indicator)
        self.listening_timer = QTimer()
        self.listening_timer.timeout.connect(self.animate_listening)
        self.listen_dots = 0

    def set_content(self, data):
        """
        data expected format:
        {
            "topic_summary": "...",
            "key_points": ["...", "..."],
            "resources": [{"title": "...", "link": "..."}]
        }
        """
        self.listening_timer.stop()
        self.set_recording_mode(False)
        self.summary_text = data.get("topic_summary", "")
        key_points = data.get("key_points", [])
        self.resources = data.get("resources", [])
        
        html = f"<h3>Summary</h3><p>{self.summary_text}</p>"
        if key_points:
            html += "<h3>Key Points</h3><ul>"
            for kp in key_points:
                html += f"<li>{kp}</li>"
            html += "</ul>"
            
        if self.resources:
            html += "<h3>Recommended Resources</h3><ul>"
            for res in self.resources:
                title = res.get("title", "Resource")
                link = res.get("link", "#")
                html += f"<li><a href='{link}' style='color: #89b4fa;'>{title}</a></li>"
            html += "</ul>"
            
        self.content_browser.setHtml(html)

    def set_loading(self, message="Searching..."):
        self.listening_timer.stop()
        self.set_recording_mode(False)
        self.content_browser.setHtml(f"<h3 style='text-align:center; color:#f38ba8;'><br><br>{message}</h3>")

    def set_recording_mode(self, is_recording):
        if is_recording:
            self.btn_copy.setVisible(False)
            self.btn_cancel_rec.setVisible(True)
            self.btn_stop_rec.setVisible(True)
            self.show_listening_ui()
        else:
            self.btn_copy.setVisible(True)
            self.btn_cancel_rec.setVisible(False)
            self.btn_stop_rec.setVisible(False)

    def show_listening_ui(self):
        self.listen_dots = 0
        self.listening_timer.start(500)
        self.animate_listening()

    def animate_listening(self):
        dots = "." * (self.listen_dots % 4)
        mic_states = ["🎙️", "🎤", "🎙️", "🎤"]
        state = mic_states[self.listen_dots % len(mic_states)]
        self.content_browser.setHtml(
            f"<div style='text-align:center; color:#a6e3a1; margin-top:80px;'>"
            f"<span style='font-size: 48px;'>{state}</span>"
            f"<h3>Voice Assistant Active</h3>"
            f"<p style='font-size: 16px;'>Listening{dots}</p>"
            f"<p style='color:#a6adc8; font-size: 12px;'>Speak now (auto-stops on 1.5s silence<br>or press hotkey again)</p>"
            f"</div>"
        )
        self.listen_dots += 1

    def show_transcribing_ui(self, message="Processing Speech..."):
        self.listening_timer.stop()
        self.content_browser.setHtml(
            f"<div style='text-align:center; color:#f9e2af; margin-top:80px;'>"
            f"<span style='font-size: 48px;'>⚙️</span>"
            f"<h3>Transcribing</h3>"
            f"<p style='font-size: 14px;'>{message}</p>"
            f"</div>"
        )

    def toggle_pin(self):
        self.pinned = self.btn_pin.isChecked()
        if self.pinned:
            self.btn_pin.setText("📍 Pinned")
        else:
            self.btn_pin.setText("📌 Pin")

    def hide_panel(self):
        self.hide()

    def copy_summary(self):
        QApplication.clipboard().setText(self.summary_text)

    def open_link(self, qurl):
        webbrowser.open(qurl.toString())

    # Drag window functionality
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos is not None:
            delta = QPoint(event.globalPosition().toPoint() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = None

class NotificationToaster(QWidget):
    def __init__(self, message="Searching... (3-5 seconds)"):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("""
            QWidget {
                background-color: #f38ba8;
                color: #1e1e2e;
                border-radius: 10px;
                padding: 10px;
                font-family: "Segoe UI", sans-serif;
                font-weight: bold;
            }
        """)
        layout = QVBoxLayout(self)
        self.label = QLabel(message)
        layout.addWidget(self.label)
        
        # Position bottom right
        screen = QGuiApplication.primaryScreen().geometry()
        self.resize(250, 50)
        self.move(screen.width() - self.width() - 20, screen.height() - self.height() - 60)
