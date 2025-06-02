# This GUI is made by Eng. Haitham Ramadan
# https://www.linkedin.com/in/haitham-ramadan-alyamani/
import sys
import os
import time
import serial
import serial.tools.list_ports
import threading
import numpy as np
from datetime import datetime
from collections import deque
import pandas as pd

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QComboBox, QPushButton, QLabel, 
                           QFrame, QSpinBox, QSplitter, QGridLayout)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QSize, QRect  # Added QRect
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QBrush, QRadialGradient, QLinearGradient, QPainterPath


import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# Dark theme color palette - Enhanced vibrant colors
DARK_BG = "#0f111a"  # Darker background
DARK_CARD_BG = "#1a1b26"  # Darker card background
TEXT_COLOR = "#e0e0ff"  # Brighter text
ACCENT_COLOR = "#7aa2f7"  # Vibrant blue
SUCCESS_COLOR = "#9ece6a"  # Vibrant green
WARNING_COLOR = "#e0af68"  # Vibrant amber
ERROR_COLOR = "#f7768e"  # Vibrant red
GRAPH_BG = "#16161e"  # Darker graph background

# Gauge colors - Enhanced vibrant
COLD_COLOR = "#73daca"  # Vibrant teal
NORMAL_COLOR = "#9ece6a"  # Vibrant green
WARM_COLOR = "#ff9e64"  # Vibrant orange
HOT_COLOR = "#f7768e"  # Vibrant red



class TemperatureGauge(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 250)  # Increased height to accommodate digital display
        self.temperature = 0.0
        self.min_temp = 0
        self.max_temp = 100
        self.unit = "°C"
        
        # For smooth animation
        self.display_temp = 0.0
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.start(16)  # ~60 FPS
        
    def update_animation(self):
        # Smooth animation
        diff = self.temperature - self.display_temp
        if abs(diff) > 0.1:
            self.display_temp += diff * 0.1
            self.update()
        elif self.display_temp != self.temperature:
            self.display_temp = self.temperature
            self.update()
            
    def set_temperature(self, temp, unit="°C"):
        self.temperature = temp
        self.unit = unit
        
    def set_range(self, min_temp, max_temp):
        self.min_temp = min_temp
        self.max_temp = max_temp
        self.update()
        
    def get_color(self, temp):
        # Map temperature to color
        if temp < 20:
            return QColor(COLD_COLOR)
        elif temp < 40:
            return QColor(NORMAL_COLOR)
        elif temp < 60:
            return QColor(WARM_COLOR)
        else:
            return QColor(HOT_COLOR)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        center_x = width / 2
        center_y = height / 2
        
        # Digital display area (top part)
        digital_height = 50
        display_rect = QRect(0, 0, width, digital_height)
        
        # Draw digital display background
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(DARK_CARD_BG))
        painter.drawRect(display_rect)
        
        # Draw digital temperature
        temp_text = f"{self.display_temp:.1f}{self.unit}"
        temp_color = self.get_color(self.display_temp)
        
        # Create a modern digital font
        digital_font = QFont("Arial", 24, QFont.Bold)
        painter.setFont(digital_font)
        text_width = painter.fontMetrics().boundingRect(temp_text).width()
        
        # Draw digital temperature with glow effect
        painter.setPen(QPen(QColor(DARK_BG), 2))  # Shadow for depth
        painter.drawText(int(center_x - text_width/2 + 2), 
                        int(digital_height/2 + 8 + 2), temp_text)
                        
        painter.setPen(QPen(temp_color, 1))  # Use temperature color
        painter.drawText(int(center_x - text_width/2), 
                        int(digital_height/2 + 8), temp_text)
        
        # Gauge size and position (below digital display)
        gauge_center_y = digital_height + (height - digital_height) / 2
        radius = min(width, height - digital_height) * 0.4
        
        # Draw outer rim
        painter.setPen(QPen(QColor(ACCENT_COLOR).darker(120), 8))
        painter.drawEllipse(int(center_x - radius - 10), int(gauge_center_y - radius - 10), 
                           int(2 * (radius + 10)), int(2 * (radius + 10)))
        
        # Draw background
        gradient = QRadialGradient(center_x, gauge_center_y, radius)
        gradient.setColorAt(0, QColor(DARK_CARD_BG).lighter(120))
        gradient.setColorAt(1, QColor(DARK_CARD_BG))
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(center_x - radius), int(gauge_center_y - radius), 
                           int(2 * radius), int(2 * radius))
        
        # Draw scale marks
        painter.setPen(QPen(QColor(TEXT_COLOR), 2))
        for i in range(11):  # 0 to 10 scale marks
            angle = 225 + i * 27  # 225 to 495 degrees (from -45 to +225)
            rad_angle = angle * np.pi / 180
            
            inner_point_x = center_x + (radius - 15) * np.cos(rad_angle)
            inner_point_y = gauge_center_y + (radius - 15) * np.sin(rad_angle)
            
            outer_point_x = center_x + radius * np.cos(rad_angle)
            outer_point_y = gauge_center_y + radius * np.sin(rad_angle)
            
            painter.drawLine(int(inner_point_x), int(inner_point_y), 
                            int(outer_point_x), int(outer_point_y))
            
            # Draw scale numbers
            if i % 2 == 0:  # Only draw every other number
                label_value = self.min_temp + (i/10) * (self.max_temp - self.min_temp)
                painter.setFont(QFont("Arial", 8))
                text_x = int(center_x + (radius - 30) * np.cos(rad_angle) - 10)
                text_y = int(gauge_center_y + (radius - 30) * np.sin(rad_angle) + 5)
                painter.drawText(text_x, text_y, f"{int(label_value)}")
        
        # Calculate needle angle
        temp_ratio = (self.display_temp - self.min_temp) / (self.max_temp - self.min_temp)
        temp_ratio = max(0, min(1, temp_ratio))  # Clamp between 0 and 1
        needle_angle = 225 + temp_ratio * 270  # Map to our scale
        
        # Draw needle
        painter.save()
        painter.translate(center_x, gauge_center_y)
        painter.rotate(needle_angle)
        
        needle_color = self.get_color(self.display_temp)
        painter.setPen(QPen(needle_color, 3))
        
        path = QPainterPath()
        path.moveTo(0, 0)
        path.lineTo(-5, 5)
        path.lineTo(radius - 10, 0)
        path.lineTo(-5, -5)
        path.closeSubpath()
        
        painter.fillPath(path, QBrush(needle_color))
        painter.drawPath(path)
        painter.restore()
        
        # Draw center cap
        painter.setBrush(QBrush(needle_color.darker(120)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(center_x - 10), int(gauge_center_y - 10), 20, 20)
        
        # Draw temperature text
        # Get temperature gradient color
        temp_color = self.get_color(self.display_temp)
        
        # Create temperature text
        temp_text = f"{self.display_temp:.1f}{self.unit}"
        
        # Calculate text width
        painter.setFont(QFont("Arial", 14, QFont.Bold))
        text_width = painter.fontMetrics().boundingRect(temp_text).width()
        
        # Draw temperature text with glow effect
        painter.setPen(QPen(QColor(DARK_BG), 2))  # Shadow for depth
        painter.drawText(int(center_x - text_width/2 + 2), 
                        int(center_y + radius + 40 + 2), temp_text)
                        
        painter.setPen(QPen(temp_color, 1))  # Use temperature color
        painter.drawText(int(center_x - text_width/2), 
                        int(center_y + radius + 40), temp_text)

class TemperatureGraph(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.fig.patch.set_facecolor(GRAPH_BG)
        
        self.axes = self.fig.add_subplot(111)
        self.axes.set_facecolor(GRAPH_BG)
        
        # Customize the grid and axes
        self.axes.grid(True, linestyle='-', alpha=0.3)
        self.axes.tick_params(colors=TEXT_COLOR)
        for spine in self.axes.spines.values():
            spine.set_color(ACCENT_COLOR)
            
        # Initialize time and temperature data
        self.times = deque(maxlen=60)  # 5 minutes at 5-second intervals
        self.temps = deque(maxlen=60)
        
        # Set up the plot
        self.line, = self.axes.plot([], [], color=ACCENT_COLOR, linewidth=2)
        self.axes.set_ylim(0, 100)
        self.axes.set_title('Temperature History', color=TEXT_COLOR)
        self.axes.set_xlabel('Time', color=TEXT_COLOR)
        self.axes.set_ylabel('Temperature (°C)', color=TEXT_COLOR)
        
        self.fig.tight_layout()
        super().__init__(self.fig)
        
    def add_data(self, temp):
        current_time = datetime.now().strftime('%H:%M:%S')
        self.times.append(current_time)
        self.temps.append(temp)
        
        # Update the plot data
        self.line.set_data(range(len(self.times)), self.temps)
        
        # Adjust x-axis
        if len(self.times) > 1:
            self.axes.set_xlim(0, len(self.times) - 1)
            
        # Adjust y-axis to fit the data with some padding
        if len(self.temps) > 0:
            min_temp = min(self.temps) - 5
            max_temp = max(self.temps) + 5
            range_temp = max_temp - min_temp
            if range_temp < 10:  # Ensure a reasonable range
                mean_temp = (min_temp + max_temp) / 2
                min_temp = mean_temp - 5
                max_temp = mean_temp + 5
            self.axes.set_ylim(min_temp, max_temp)
            
        # Add x-ticks at regular intervals
        if len(self.times) > 1:
            num_ticks = min(5, len(self.times))
            step = max(1, len(self.times) // num_ticks)
            tick_positions = list(range(0, len(self.times), step))
            tick_labels = [self.times[i] for i in tick_positions]
            self.axes.set_xticks(tick_positions)
            self.axes.set_xticklabels(tick_labels, rotation=45)
            
        self.fig.tight_layout()
        self.draw()
        
    def set_unit(self, unit):
        self.axes.set_ylabel(f'Temperature ({unit})', color=TEXT_COLOR)
        self.draw()

class StatusIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.status = "disconnected"  # disconnected, connecting, connected, error
        self.message = "Disconnected"
        self.setMinimumSize(15, 15)
        self.setMaximumSize(15, 15)
        
    def set_status(self, status, message=""):
        self.status = status
        self.message = message
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if self.status == "disconnected":
            color = QColor(TEXT_COLOR)
        elif self.status == "connecting":
            color = QColor(WARNING_COLOR)
        elif self.status == "connected":
            color = QColor(SUCCESS_COLOR)
        else:  # error
            color = QColor(ERROR_COLOR)
            
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(2, 2, 11, 11)
        
        # Add a subtle glow effect
        if self.status in ["connected", "error"]:
            for i in range(3):
                alpha = 100 - i * 30
                glow_color = QColor(color)
                glow_color.setAlpha(alpha)
                painter.setPen(QPen(glow_color, i*2))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(2-i, 2-i, 11+i*2, 11+i*2)

class SerialManager(QObject):
    temperature_update = pyqtSignal(float)
    connection_status = pyqtSignal(str, str)
    
    def __init__(self):
        super().__init__()
        self.serial = None
        self.running = False
        self.thread = None
        self.data_buffer = []
        
    def connect(self, port, baudrate=9600):
        try:
            self.connection_status.emit("connecting", f"Connecting to {port}...")
            self.serial = serial.Serial(port, baudrate, timeout=1)
            self.running = True
            self.thread = threading.Thread(target=self.read_loop, daemon=True)
            self.thread.start()
            return True
        except Exception as e:
            self.connection_status.emit("error", f"Connection error: {str(e)}")
            return False
            
    def disconnect(self):
        self.running = False
        if self.thread:
            self.thread.join(1.0)
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.serial = None
        self.connection_status.emit("disconnected", "Disconnected")
        
    def read_loop(self):
        self.connection_status.emit("connected", "Connected")
        while self.running and self.serial and self.serial.is_open:
            try:
                if self.serial.in_waiting > 0:
                    data = self.serial.readline().decode('utf-8').strip()
                    try:
                        # Try to parse temperature value
                        temp = float(data)
                        self.temperature_update.emit(temp)
                        self.data_buffer.append((datetime.now(), temp))
                    except ValueError:
                        pass
            except Exception as e:
                self.connection_status.emit("error", f"Read error: {str(e)}")
                break
            time.sleep(0.1)
        
        # If we broke out of the loop due to an error but running is still True
        if self.running:
            self.disconnect()

class DataLogger:
    def __init__(self):
        self.data = []
        self.last_save_time = time.time()
        self.save_interval = 5  # seconds
        self.filename = self.get_next_available_filename()
        self.session_data = []  # To store all readings for this session
        
    def get_next_available_filename(self):
        base_name = "temperature_log"
        extension = ".xlsx"
        counter = 1
        
        while True:
            filename = f"{base_name}{counter}{extension}"
            if not os.path.exists(filename):
                return filename
            counter += 1
            
    def add_data(self, temp, is_celsius):
        timestamp = datetime.now()
        unit = "°C" if is_celsius else "°F"
        new_entry = {"Timestamp": timestamp, "Temperature": temp, "Unit": unit}
        
        # Add to both temporary buffer and session data
        self.data.append(new_entry)
        self.session_data.append(new_entry)
        
        # Check if we should save to Excel
        current_time = time.time()
        if current_time - self.last_save_time >= self.save_interval:
            self.save_to_excel()
            self.last_save_time = current_time
            return self.filename
        return None
            
    def save_to_excel(self):
        if not self.session_data:  # Use session_data instead of data
            return None
            
        try:
            # Create DataFrame from all session data
            df = pd.DataFrame(self.session_data)
            
            # Save to current directory
            df.to_excel(self.filename, index=False)
            
            # Clear only the temporary buffer
            self.data = []
            
            # Return full path for display
            full_path = os.path.abspath(self.filename)
            return full_path
        except Exception as e:
            print(f"Error saving to Excel: {str(e)}")
            return None
            
    def final_save(self):
        """Save all remaining data when closing the application"""
        if self.data:  # Save any unsaved data
            self.save_to_excel()

class StylishCard(QFrame):
    def __init__(self, title=None, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        # Apply enhanced card style with subtle gradient and glow
        self.setStyleSheet(f"""
            StylishCard {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                stop:0 {DARK_CARD_BG}, 
                                                stop:1 {DARK_BG});
                border-radius: 12px;
                border: 2px solid {ACCENT_COLOR};
                margin: 5px;
            }}
        """)
        
        # Add drop shadow effect
        shadow = self.style().standardPixmap(self.style().SP_TitleBarShadeButton)
        
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)
        
        # Add title if provided
        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet(f"""
                font-size: 18px;
                font-weight: bold;
                color: {ACCENT_COLOR};
                padding-bottom: 5px;
                border-bottom: 1px solid {ACCENT_COLOR};
            """)
            self.layout.addWidget(title_label)
            self.layout.addSpacing(5)

class TemperatureMonitorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CI Project - Temperature Monitor")
        self.resize(900, 600)
        
        # Set app style
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {DARK_BG};
                color: {TEXT_COLOR};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            QLabel {{
                color: {TEXT_COLOR};
            }}
            QPushButton {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                stop:0 {DARK_CARD_BG}, 
                                                stop:1 {DARK_BG});
                color: {TEXT_COLOR};
                border: 2px solid {ACCENT_COLOR};
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {ACCENT_COLOR};
                color: {DARK_BG};
            }}
            QPushButton:pressed {{
                background-color: {ACCENT_COLOR.lower()};
                padding: 7px 11px;
            }}
            QComboBox, QSpinBox {{
                background-color: {DARK_CARD_BG};
                color: {TEXT_COLOR};
                border: 2px solid {ACCENT_COLOR};
                border-radius: 6px;
                padding: 6px;
                min-height: 20px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 6px solid {ACCENT_COLOR};
                width: 0;
                height: 0;
                margin-right: 8px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {DARK_BG};
                color: {TEXT_COLOR};
                selection-background-color: {ACCENT_COLOR};
                selection-color: {DARK_BG};
                border: 2px solid {ACCENT_COLOR};
            }}
            QStatusBar {{
                background-color: {DARK_CARD_BG};
                color: {TEXT_COLOR};
                font-weight: bold;
                border-top: 2px solid {ACCENT_COLOR};
            }}
        """)
        
        
        # Initialize variables
        self.is_celsius = True
        self.temp_celsius = 0.0
        
        # Serial connection manager
        self.serial_manager = SerialManager()
        self.serial_manager.temperature_update.connect(self.update_temperature)
        self.serial_manager.connection_status.connect(self.update_connection_status)
        
        # Data logger
        self.data_logger = DataLogger()
        
        # Create central widget and layout
        self.central_widget = QWidget()
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.setCentralWidget(self.central_widget)
        
        # Create top section with controls
        self.create_control_section()
        
        # Create main content area with splitter
        self.splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(self.splitter)
        
        # Create left panel with gauge
        self.create_gauge_panel()
        
        # Create right panel with graph
        self.create_graph_panel()
        
        # Create status bar
        self.status_bar = self.statusBar()
        self.status_bar.setStyleSheet(f"background-color: {DARK_CARD_BG}; color: {TEXT_COLOR};")
        
        self.status_indicator = StatusIndicator()
        self.status_message = QLabel("Disconnected")
        
        status_layout = QHBoxLayout()
        status_layout.addWidget(self.status_indicator)
        status_layout.addWidget(self.status_message)
        
        status_widget = QWidget()
        status_widget.setLayout(status_layout)
        self.status_bar.addPermanentWidget(status_widget)
        
        # Initialize available ports
        self.refresh_ports()
        
        # Start refresh timer for ports
        self.port_refresh_timer = QTimer(self)
        self.port_refresh_timer.timeout.connect(self.refresh_ports)
        self.port_refresh_timer.start(5000)  # Refresh every 5 seconds
        
    def create_control_section(self):
        control_card = StylishCard()
        control_layout = QHBoxLayout()
        control_card.layout.addLayout(control_layout)
        
        # Port selection with label
        port_layout = QVBoxLayout()
        port_label = QLabel("COM Port:")
        port_label.setStyleSheet(f"color: {ACCENT_COLOR}; font-weight: bold;")
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(120)
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.port_combo)
        control_layout.addLayout(port_layout)
        
        # Refresh ports button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setIcon(self.style().standardIcon(self.style().SP_BrowserReload))
        self.refresh_btn.clicked.connect(self.refresh_ports)
        control_layout.addWidget(self.refresh_btn)
        
        # Baud rate with label
        baud_layout = QVBoxLayout()
        baud_label = QLabel("Baud Rate:")
        baud_label.setStyleSheet(f"color: {ACCENT_COLOR}; font-weight: bold;")
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["4800", "9600", "19200", "38400", "57600", "115200"])
        self.baud_combo.setCurrentText("4800")  # Match your original code
        baud_layout.addWidget(baud_label)
        baud_layout.addWidget(self.baud_combo)
        control_layout.addLayout(baud_layout)
        
        # Sampling interval with label
        interval_layout = QVBoxLayout()
        interval_label = QLabel("Log Interval (sec):")
        interval_label.setStyleSheet(f"color: {ACCENT_COLOR}; font-weight: bold;")
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 60)
        self.interval_spin.setValue(5)
        self.interval_spin.valueChanged.connect(self.update_log_interval)
        interval_layout.addWidget(interval_label)
        interval_layout.addWidget(self.interval_spin)
        control_layout.addLayout(interval_layout)
        
        # Add spacer
        control_layout.addStretch()
        
        # Connect/Disconnect button
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setMinimumWidth(100)
        self.connect_btn.clicked.connect(self.toggle_connection)
        self.connect_btn.setStyleSheet(f"""
            font-weight: bold;
            padding: 8px;
        """)
        control_layout.addWidget(self.connect_btn)
        
        # Temperature unit toggle button
        self.unit_btn = QPushButton("°C → °F")
        self.unit_btn.setMinimumWidth(100)
        self.unit_btn.clicked.connect(self.toggle_temperature_unit)
        self.unit_btn.setStyleSheet(f"""
            font-weight: bold;
            padding: 8px;
        """)
        control_layout.addWidget(self.unit_btn)
        
        self.main_layout.addWidget(control_card)
        
    def create_gauge_panel(self):
        gauge_panel = StylishCard("Temperature Gauge")
        gauge_layout = QVBoxLayout()
        gauge_panel.layout.addLayout(gauge_layout)
        
        # Create temperature gauge
        self.gauge = TemperatureGauge()
        gauge_layout.addWidget(self.gauge)
        
        self.splitter.addWidget(gauge_panel)
        
    def create_graph_panel(self):
        graph_panel = StylishCard("Temperature History")
        graph_layout = QVBoxLayout()
        graph_panel.layout.addLayout(graph_layout)
        
        # Create temperature graph
        self.graph = TemperatureGraph()
        graph_layout.addWidget(self.graph)
        
        self.splitter.addWidget(graph_panel)
        
    def refresh_ports(self):
        current_port = self.port_combo.currentText()
        
        # Get available ports from system
        available_ports = [port.device for port in serial.tools.list_ports.comports()]
        
        # If no ports found, add manual options from COM1 to COM10
        if not available_ports:
            available_ports = ["COM1", "COM2", "COM3", "COM4", "COM5", 
                            "COM6", "COM7", "COM8", "COM9", "COM10"]
        
        # Update combo box
        self.port_combo.clear()
        self.port_combo.addItems(available_ports)
        
        # Try to restore previously selected port if it exists
        index = self.port_combo.findText(current_port)
        if index >= 0:
            self.port_combo.setCurrentIndex(index)
            
    def toggle_connection(self):
        if self.connect_btn.text() == "Connect":
            port = self.port_combo.currentText()
            baudrate = int(self.baud_combo.currentText())
            
            if self.serial_manager.connect(port, baudrate):
                self.connect_btn.setText("Disconnect")
                self.connect_btn.setStyleSheet(f"""
                    background-color: {ERROR_COLOR};
                    color: {DARK_BG};
                    border: 1px solid {ERROR_COLOR};
                    border-radius: 5px;
                    padding: 5px 10px;
                """)
        else:
            self.serial_manager.disconnect()
            self.connect_btn.setText("Connect")
            self.connect_btn.setStyleSheet("")  # Reset to default style
            
    def update_connection_status(self, status, message):
        self.status_indicator.set_status(status)
        self.status_message.setText(message)
        
        if status == "connected":
            self.connect_btn.setText("Disconnect")
            self.connect_btn.setStyleSheet(f"""
                background-color: {ERROR_COLOR};
                color: {DARK_BG};
                border: 1px solid {ERROR_COLOR};
                border-radius: 5px;
                padding: 5px 10px;
            """)
        elif status == "disconnected" or status == "error":
            self.connect_btn.setText("Connect")
            self.connect_btn.setStyleSheet("")  # Reset to default style
            
    def update_temperature(self, temp):
        # Store temperature in Celsius
        self.temp_celsius = temp
        
        # Convert if necessary
        display_temp = temp if self.is_celsius else (temp * 9/5) + 32
        unit = "°C" if self.is_celsius else "°F"
        
        # Update gauge
        self.gauge.set_temperature(display_temp, unit)
        
        # Update graph
        self.graph.add_data(display_temp)
        
        # Log data
        log_file = self.data_logger.add_data(display_temp, self.is_celsius)
        if log_file:
            self.status_message.setText(f"Data saved to: {log_file}")
        
    def toggle_temperature_unit(self):
        self.is_celsius = not self.is_celsius
        
        if self.is_celsius:
            self.unit_btn.setText("°C → °F")
            display_temp = self.temp_celsius
            unit = "°C"
        else:
            self.unit_btn.setText("°F → °C")
            display_temp = (self.temp_celsius * 9/5) + 32
            unit = "°F"
            
        # Update gauge
        self.gauge.set_temperature(display_temp, unit)
        
        # Update graph y-axis label
        self.graph.set_unit(unit)
        
    def update_log_interval(self, value):
        self.data_logger.save_interval = value

def main():
    app = QApplication(sys.argv)
    window = TemperatureMonitorApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()