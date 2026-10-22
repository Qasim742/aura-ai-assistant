import sys
import random
from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QLinearGradient, QPainterPath
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QFrame
)

# --- Futuristic Neon Cyberpunk Theme ---
THEME_STYLE = """
QMainWindow {
    background-color: #030712;
}
QWidget {
    color: #f8fafc;
    font-family: 'Segoe UI', -apple-system, sans-serif;
}
/* Outer Sci-Fi Dashboard Frame */
#DashboardFrame {
    background-color: #060b19;
    border: 2px solid #38bdf8;
    border-radius: 16px;
}
/* Glassmorphism Cards */
.QFrame#GlassCard {
    background-color: rgba(15, 23, 42, 0.85);
    border: 1px solid #1e3a8a;
    border-radius: 12px;
}
/* Top Header Banner */
#HeaderTitle {
    color: #38bdf8;
    font-size: 16px;
    font-weight: 700;
    letter-spacing: 2px;
}
/* Buttons */
QPushButton.SciFiBtn {
    background-color: rgba(30, 58, 138, 0.4);
    color: #38bdf8;
    border: 1px solid #38bdf8;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 12px;
}
QPushButton.SciFiBtn:hover {
    background-color: rgba(56, 189, 248, 0.2);
    color: #f8fafc;
}
"""

class RobotAvatarWidget(QWidget):
    """Custom painted futuristic robot head with glowing happy eyes and animated waveform mouth."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 300)
        self.mouth_offset = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(45)

    def animate(self):
        self.mouth_offset = random.uniform(-4, 4)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        cx = width / 2.0
        cy = height / 2.0

        # Outer Holographic Glow Aura
        glow_grad = QLinearGradient(cx, cy - 120, cx, cy + 120)
        glow_grad.setColorAt(0.0, QColor(56, 189, 248, 80))
        glow_grad.setColorAt(1.0, QColor(168, 85, 247, 30))
        painter.setBrush(QBrush(glow_grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(cx - 130, cy - 130, 260, 260))

        # Robot Head Shell (Rounded cute bot shape)
        head_rect = QRectF(cx - 95, cy - 95, 190, 175)
        painter.setBrush(QBrush(QColor("#0a0f1d")))
        painter.setPen(QPen(QColor("#38bdf8"), 3))
        painter.drawRoundedRect(head_rect, 55, 55)

        # Ears / Side pods
        painter.setBrush(QBrush(QColor("#1e293b")))
        painter.setPen(QPen(QColor("#38bdf8"), 2))
        painter.drawRoundedRect(QRectF(cx - 118, cy - 30, 22, 55), 8, 8)
        painter.drawRoundedRect(QRectF(cx + 96, cy - 30, 22, 55), 8, 8)

        # Happy Glowing Eyes (^ ^)
        eye_pen = QPen(QColor("#38bdf8"), 5, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(eye_pen)
        painter.setBrush(Qt.NoPen)
        
        # Left eye arc (^ curve)
        painter.drawArc(QRectF(cx - 50, cy - 35, 32, 24), 0, 180 * 16)
        # Right eye arc (^ curve)
        painter.drawArc(QRectF(cx + 18, cy - 35, 32, 24), 0, 180 * 16)

        # Neon Waveform Mouth
        mouth_pen = QPen(QColor("#c084fc"), 4, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(mouth_pen)
        
        path = QPainterPath()
        start_x = cx - 42
        start_y = cy + 28
        path.moveTo(start_x, start_y)
        
        # Dynamic active speech waveform
        path.cubicTo(cx - 20, start_y + 16 + self.mouth_offset,
                     cx - 7, start_y - 16 - self.mouth_offset,
                     cx + 7, start_y + 14 + self.mouth_offset)
        path.cubicTo(cx + 20, start_y - 14 - self.mouth_offset,
                     cx + 30, start_y + 16 + self.mouth_offset,
                     cx + 42, start_y)
        painter.drawPath(path)


class LiveAudioVisualizer(QWidget):
    """Live audio frequency spectrum visualizer bars."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(110)
        self.bars = [random.randint(15, 80) for _ in range(24)]
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_bars)
        self.timer.start(80)

    def update_bars(self):
        self.bars = [random.randint(20, 90) for _ in range(24)]
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        bar_width = max(3, (width / len(self.bars)) - 4)
        
        for i, val in enumerate(self.bars):
            x = i * (bar_width + 4) + 6
            bar_height = (val / 100.0) * (height - 20)
            y = height - bar_height - 10
            
            grad = QLinearGradient(x, y, x, y + bar_height)
            grad.setColorAt(0.0, QColor("#38bdf8"))
            grad.setColorAt(1.0, QColor("#7c3aed"))
            
            painter.setBrush(QBrush(grad))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(QRectF(x, y, bar_width, bar_height), 2, 2)


class AuraDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AURA — AI Assistant Dashboard")
        self.resize(1200, 720)
        self.setStyleSheet(THEME_STYLE)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # Outer dashboard container with sci-fi border
        dashboard = QFrame()
        dashboard.setObjectName("DashboardFrame")
        dash_layout = QVBoxLayout(dashboard)
        dash_layout.setContentsMargins(24, 20, 24, 20)
        dash_layout.setSpacing(16)

        # --- 1. Top Header ---
        header_layout = QHBoxLayout()
        header_title = QLabel("AURA AI ASSISTANT")
        header_title.setObjectName("HeaderTitle")
        header_layout.addWidget(header_title)
        header_layout.addStretch()
        dash_layout.addLayout(header_layout)

        # --- 2. Main Body (Split into Left Avatar & Right Widgets) ---
        body_layout = QHBoxLayout()
        body_layout.setSpacing(20)

        # Left Side: Robot Avatar & Greeting
        left_card = QFrame()
        left_card.setObjectName("GlassCard")
        left_layout = QVBoxLayout(left_card)
        left_layout.setAlignment(Qt.AlignCenter)
        left_layout.setSpacing(12)

        self.robot_widget = RobotAvatarWidget()
        left_layout.addWidget(self.robot_widget, alignment=Qt.AlignCenter)

        name_lbl = QLabel("AURA AI")
        name_lbl.setStyleSheet("font-size: 20px; font-weight: bold; color: #38bdf8; letter-spacing: 1px;")
        left_layout.addWidget(name_lbl, alignment=Qt.AlignCenter)

        subtitle_lbl = QLabel("Hi! How can I help you today?")
        subtitle_lbl.setStyleSheet("font-size: 13px; color: #94a3b8;")
        left_layout.addWidget(subtitle_lbl, alignment=Qt.AlignCenter)

        body_layout.addWidget(left_card, 55)

        # Right Side: Stack of 3 Futuristic Widgets
        right_layout = QVBoxLayout()
        right_layout.setSpacing(14)

        # Widget 1: Live Audio Input & Waveform
        audio_card = QFrame()
        audio_card.setObjectName("GlassCard")
        ac_layout = QVBoxLayout(audio_card)
        ac_layout.setContentsMargins(16, 14, 16, 14)
        
        audio_header = QHBoxLayout()
        audio_title = QLabel("LIVE AUDIO INPUT")
        audio_title.setStyleSheet("font-size: 11px; font-weight: bold; color: #64748b; letter-spacing: 1px;")
        audio_header.addWidget(audio_title)
        audio_header.addStretch()
        
        mic_icon_lbl = QLabel("🎙️")
        audio_header.addWidget(mic_icon_lbl)
        ac_layout.addLayout(audio_header)

        self.visualizer = LiveAudioVisualizer()
        ac_layout.addWidget(self.visualizer)
        right_layout.addWidget(audio_card)

        # Widget 2: Weather / System Widget
        weather_card = QFrame()
        weather_card.setObjectName("GlassCard")
        wc_layout = QVBoxLayout(weather_card)
        wc_layout.setContentsMargins(16, 14, 16, 14)
        wc_layout.setSpacing(6)

        w_header = QLabel("SYSTEM / ENVIRONMENT")
        w_header.setStyleSheet("font-size: 11px; font-weight: bold; color: #64748b; letter-spacing: 1px;")
        wc_layout.addWidget(w_header)

        w_info_layout = QHBoxLayout()
        w_text = QLabel("<b>Peshawar, Pakistan</b><br><span style='color: #94a3b8; font-size: 12px;'>Connected & Optimized</span>")
        w_temp = QLabel("<b>24°C</b>")
        w_temp.setStyleSheet("font-size: 24px; color: #38bdf8;")
        w_info_layout.addWidget(w_text)
        w_info_layout.addStretch()
        w_info_layout.addWidget(w_temp)
        wc_layout.addLayout(w_info_layout)

        right_layout.addWidget(weather_card)

        # Widget 3: Voice Status Widget
        status_card = QFrame()
        status_card.setObjectName("GlassCard")
        sc_layout = QVBoxLayout(status_card)
        sc_layout.setContentsMargins(16, 14, 16, 14)

        s_header = QLabel("VOICE STATUS")
        s_header.setStyleSheet("font-size: 11px; font-weight: bold; color: #64748b; letter-spacing: 1px;")
        sc_layout.addWidget(s_header)

        s_status_row = QHBoxLayout()
        
        dot_label = QLabel("🟢")
        dot_label.setStyleSheet("font-size: 10px;")
        
        status_text = QLabel("<b>ACTIVE</b> | Listening (Groq Whisper)")
        status_text.setStyleSheet("font-size: 12px; color: #e2e8f0;")
        
        s_status_row.addWidget(dot_label)
        s_status_row.addWidget(status_text)
        s_status_row.addStretch()
        
        mic_badge = QLabel("🎤 ON")
        mic_badge.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 11px;")
        s_status_row.addWidget(mic_badge)
        
        sc_layout.addLayout(s_status_row)
        right_layout.addWidget(status_card)

        body_layout.addLayout(right_layout, 45)
        dash_layout.addLayout(body_layout)

        # --- 3. Bottom Controls / Settings & Help ---
        bottom_bar = QHBoxLayout()
        bottom_bar.addStretch()

        self.btn_settings = QPushButton("⚙️ SETTINGS")
        self.btn_settings.setObjectName("SciFiBtn")
        self.btn_settings.setCursor(Qt.PointingHandCursor)

        self.btn_help = QPushButton("ℹ️ HELP")
        self.btn_help.setObjectName("SciFiBtn")
        self.btn_help.setCursor(Qt.PointingHandCursor)

        bottom_bar.addWidget(self.btn_settings)
        bottom_bar.addWidget(self.btn_help)
        dash_layout.addLayout(bottom_bar)

        main_layout.addWidget(dashboard)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AuraDashboard()
    window.show()
    sys.exit(app.exec())