import sys
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QSlider, QPushButton, 
                             QComboBox, QGroupBox, QTextEdit, QCheckBox,
                             QSpinBox, QFrame, QGridLayout, QLineEdit, QRadioButton,
                             QButtonGroup)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon, QPainter, QPen, QBrush
import datetime


class DutyCycleGraph(QWidget):
    """Custom widget to display duty cycle waveform"""
    def __init__(self):
        super().__init__()
        self.duty_cycle = 0
        self.pwm_value = 0
        self.setMinimumHeight(150)
        
    def set_duty_cycle(self, value, pwm_value):
        """Update duty cycle value (0-100) and PWM value"""
        self.duty_cycle = value
        self.pwm_value = pwm_value
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor("#ffffff"))
        
        # Draw border
        painter.setPen(QPen(QColor("#cccccc"), 2))
        painter.drawRect(self.rect())
        
        if self.width() < 50 or self.height() < 50:
            return
        
        # Calculate waveform dimensions
        margin_left = 40
        margin_right = 20
        margin_top = 50
        margin_bottom = 40
        
        wave_width = self.width() - margin_left - margin_right
        wave_height = self.height() - margin_top - margin_bottom
        
        # Draw grid lines
        painter.setPen(QPen(QColor("#e0e0e0"), 1))
        for i in range(5):
            y = margin_top + (wave_height * i // 4)
            painter.drawLine(margin_left, y, self.width() - margin_right, y)
        
        # Draw vertical grid lines
        for i in range(5):
            x = margin_left + (wave_width * i // 4)
            painter.drawLine(x, margin_top, x, margin_top + wave_height)
        
        # Draw axes
        painter.setPen(QPen(QColor("#000000"), 2))
        painter.drawLine(margin_left, margin_top, margin_left, margin_top + wave_height)
        painter.drawLine(margin_left, margin_top + wave_height, 
                        self.width() - margin_right, margin_top + wave_height)
        
        # Draw Y-axis labels
        painter.setPen(QColor("#000000"))
        painter.setFont(QFont("Arial", 9))
        painter.drawText(5, margin_top + 5, "1")
        painter.drawText(5, margin_top + wave_height + 5, "0")
        
        # Draw X-axis labels
        painter.drawText(margin_left - 10, margin_top + wave_height + 20, "0.00")
        painter.drawText(margin_left + wave_width // 4 - 15, margin_top + wave_height + 20, "0.25")
        painter.drawText(margin_left + wave_width // 2 - 15, margin_top + wave_height + 20, "0.50")
        painter.drawText(margin_left + 3 * wave_width // 4 - 15, margin_top + wave_height + 20, "0.75")
        painter.drawText(self.width() - margin_right - 15, margin_top + wave_height + 20, "1.00")
        
        # Draw X-axis title
        painter.setFont(QFont("Arial", 10))
        x_title = "Normalized Time (2µs period)"
        title_width = painter.fontMetrics().width(x_title)
        painter.drawText((self.width() - title_width) // 2, self.height() - 5, x_title)
        
        # Draw duty cycle waveform (single period normalized)
        painter.setPen(QPen(QColor("#0066cc"), 3))
        painter.setBrush(Qt.NoBrush)
        
        high_width = int(wave_width * self.duty_cycle / 100)
        low_width = wave_width - high_width
        
        # Draw the waveform
        x_start = margin_left
        y_high = margin_top
        y_low = margin_top + wave_height
        
        # Rising edge
        painter.drawLine(x_start, y_low, x_start, y_high)
        
        # High portion
        if high_width > 0:
            painter.drawLine(x_start, y_high, x_start + high_width, y_high)
            # Falling edge
            painter.drawLine(x_start + high_width, y_high, x_start + high_width, y_low)
        
        # Low portion
        if low_width > 0:
            painter.drawLine(x_start + high_width, y_low, 
                           x_start + wave_width, y_low)
        
        # Draw title with duty cycle and value
        painter.setPen(QColor("#000000"))
        painter.setFont(QFont("Arial", 11, QFont.Bold))
        title_text = f"PWM Output = {self.duty_cycle:.2f}% Duty Cycle (Value: {self.pwm_value})"
        title_width = painter.fontMetrics().width(title_text)
        painter.drawText((self.width() - title_width) // 2, 25, title_text)


class FPGAControlGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.serial_port = None
        self.auto_refresh_timer = QTimer()
        self.auto_refresh_timer.timeout.connect(self.refresh_ports)
        self.sent_count = 0
        
        self.init_ui()
        self.refresh_ports()
        self.auto_refresh_timer.start(3000)
        
    def init_ui(self):
        self.setWindowTitle("FPGA UART Control Center")
        self.setGeometry(100, 100, 1000, 700)
        
        self.set_soft_theme()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Title
        title = QLabel("📌 FPGA UART Control Interface")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #5BA3D0; margin: 5px;")
        main_layout.addWidget(title)
        
        # Top section: Connection + Control + Graph
        top_layout = QHBoxLayout()
        top_layout.setSpacing(12)
        
        # Connection Panel (with manual port option)
        connection_group = self.create_connection_panel()
        top_layout.addWidget(connection_group, 1)
        
        # Control Panel
        control_group = self.create_control_panel()
        top_layout.addWidget(control_group, 2)
        
        # Duty Cycle Graph
        graph_group = self.create_graph_panel()
        top_layout.addWidget(graph_group, 2)
        
        main_layout.addLayout(top_layout)
        
        # Monitor Panel
        monitor_group = self.create_monitor_panel()
        main_layout.addWidget(monitor_group)
        
        # Status Bar
        self.statusBar().showMessage("Ready - Disconnected")
        self.statusBar().setStyleSheet("background-color: #3a3f47; color: #b8bcc4;")
        
    def set_soft_theme(self):
        soft_stylesheet = """
        QMainWindow {
            background-color: #2c3139;
        }
        QGroupBox {
            border: 2px solid #4a5059;
            border-radius: 8px;
            margin-top: 12px;
            font-weight: bold;
            color: #7eb8da;
            padding: 12px;
            background-color: #353a42;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 15px;
            padding: 0 5px;
        }
        QLabel {
            color: #d4d7dc;
            font-size: 10pt;
        }
        QComboBox, QSpinBox, QLineEdit {
            background-color: #3a3f47;
            border: 2px solid #4a5059;
            border-radius: 4px;
            padding: 5px;
            color: #d4d7dc;
            font-size: 9pt;
            min-height: 20px;
            selection-background-color: #5BA3D0;
            selection-color: #ffffff;
        }
        QComboBox QAbstractItemView {
            background-color: #2c3139;
            border: 2px solid #5BA3D0;
            selection-background-color: #5BA3D0;
            selection-color: #ffffff;
            color: #d4d7dc;
        }

        QComboBox:hover, QSpinBox:hover, QLineEdit:hover {
            border: 2px solid #7eb8da;
        }
        QComboBox:disabled, QSpinBox:disabled, QLineEdit:disabled {
            background-color: #2a2f36;
            color: #6a6d74;
        }
        QPushButton {
            background-color: #5BA3D0;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 8px 15px;
            font-size: 9pt;
            font-weight: bold;
            min-height: 30px;
        }
        QPushButton:hover {
            background-color: #6bb3e0;
        }
        QPushButton:pressed {
            background-color: #4b93c0;
        }
        QPushButton:disabled {
            background-color: #4a5059;
            color: #7a7d84;
        }
        QPushButton#disconnect_btn {
            background-color: #e07b7b;
        }
        QPushButton#disconnect_btn:hover {
            background-color: #f08b8b;
        }
        QPushButton#refresh_btn {
            background-color: #7dc993;
        }
        QPushButton#refresh_btn:hover {
            background-color: #8dd9a3;
        }
        QSlider::groove:horizontal {
            background: #4a5059;
            height: 8px;
            border-radius: 4px;
        }
        QSlider::handle:horizontal {
            background: #7eb8da;
            width: 18px;
            height: 18px;
            margin: -5px 0;
            border-radius: 9px;
        }
        QSlider::handle:horizontal:hover {
            background: #8ec8ea;
        }
        QSlider::sub-page:horizontal {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #6ba8d0, stop:1 #8ec8ea);
            border-radius: 4px;
        }
        QTextEdit {
            background-color: #2a2f36;
            border: 2px solid #4a5059;
            border-radius: 5px;
            color: #c0c4ca;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 9pt;
            padding: 5px;
        }
        QCheckBox, QRadioButton {
            color: #d4d7dc;
            spacing: 6px;
        }
        QCheckBox::indicator, QRadioButton::indicator {
            width: 16px;
            height: 16px;
            border-radius: 3px;
            border: 2px solid #4a5059;
            background-color: #3a3f47;
        }
        QCheckBox::indicator:checked, QRadioButton::indicator:checked {
            background-color: #7eb8da;
            border: 2px solid #7eb8da;
        }
        QRadioButton::indicator {
            border-radius: 8px;
        }
        """
        self.setStyleSheet(soft_stylesheet)
        
    def create_connection_panel(self):
        """Connection panel with manual port option"""
        group = QGroupBox("📡 Connection")
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        # Port selection method radio buttons
        self.port_mode_group = QButtonGroup()
        self.auto_port_radio = QRadioButton("Auto-detect Port")
        self.manual_port_radio = QRadioButton("Manual Port Entry")
        self.auto_port_radio.setChecked(True)
        
        self.port_mode_group.addButton(self.auto_port_radio)
        self.port_mode_group.addButton(self.manual_port_radio)
        
        self.auto_port_radio.toggled.connect(self.on_port_mode_changed)
        
        layout.addWidget(self.auto_port_radio)
        layout.addWidget(self.manual_port_radio)
        
        # Auto Port Selection
        auto_port_layout = QHBoxLayout()
        auto_port_layout.addWidget(QLabel("Port:"))
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(150)
        auto_port_layout.addWidget(self.port_combo, 1)
        
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setObjectName("refresh_btn")
        self.refresh_btn.clicked.connect(self.refresh_ports)
        self.refresh_btn.setMaximumWidth(35)
        auto_port_layout.addWidget(self.refresh_btn)
        layout.addLayout(auto_port_layout)
        
        # Manual Port Entry
        manual_port_layout = QHBoxLayout()
        manual_port_layout.addWidget(QLabel("Manual Port:"))
        self.manual_port_input = QLineEdit()
        self.manual_port_input.setPlaceholderText("e.g., COM1, COM3, /dev/ttyUSB0")
        self.manual_port_input.setEnabled(False)
        manual_port_layout.addWidget(self.manual_port_input, 1)
        layout.addLayout(manual_port_layout)
        
        # Baud Rate
        baud_layout = QHBoxLayout()
        baud_layout.addWidget(QLabel("Baud:"))
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.baud_combo.setCurrentText("9600")
        baud_layout.addWidget(self.baud_combo, 1)
        layout.addLayout(baud_layout)
        
        # Config (single line)
        config_layout = QHBoxLayout()
        self.databits_combo = QComboBox()
        self.databits_combo.addItems(["5", "6", "7", "8"])
        self.databits_combo.setCurrentText("8")
        config_layout.addWidget(QLabel("Data:"))
        config_layout.addWidget(self.databits_combo)
        
        self.parity_combo = QComboBox()
        self.parity_combo.addItems(["None", "Even", "Odd"])
        config_layout.addWidget(QLabel("Parity:"))
        config_layout.addWidget(self.parity_combo)
        
        self.stopbits_combo = QComboBox()
        self.stopbits_combo.addItems(["1", "2"])
        config_layout.addWidget(QLabel("Stop:"))
        config_layout.addWidget(self.stopbits_combo)
        layout.addLayout(config_layout)
        
        # Connect buttons
        button_layout = QHBoxLayout()
        self.connect_btn = QPushButton("⚡ Connect")
        self.connect_btn.clicked.connect(self.connect_serial)
        button_layout.addWidget(self.connect_btn)
        
        self.disconnect_btn = QPushButton("✕")
        self.disconnect_btn.setObjectName("disconnect_btn")
        self.disconnect_btn.clicked.connect(self.disconnect_serial)
        self.disconnect_btn.setEnabled(False)
        self.disconnect_btn.setMaximumWidth(40)
        button_layout.addWidget(self.disconnect_btn)
        layout.addLayout(button_layout)
        
        # Status indicator
        self.status_indicator = QLabel("● Disconnected")
        self.status_indicator.setStyleSheet("color: #e07b7b; font-weight: bold;")
        self.status_indicator.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_indicator)
        
        group.setLayout(layout)
        return group
    
    def on_port_mode_changed(self):
        """Handle port mode radio button change"""
        if self.auto_port_radio.isChecked():
            self.port_combo.setEnabled(True)
            self.refresh_btn.setEnabled(True)
            self.manual_port_input.setEnabled(False)
        else:
            self.port_combo.setEnabled(False)
            self.refresh_btn.setEnabled(False)
            self.manual_port_input.setEnabled(True)
    
    def create_control_panel(self):
        group = QGroupBox("🎛️ PWM Control")
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        # Value display
        value_layout = QHBoxLayout()
        self.value_display = QLabel("0")
        self.value_display.setFont(QFont("Segoe UI", 28, QFont.Bold))
        self.value_display.setStyleSheet("color: #7eb8da; background-color: #2a2f36; "
                                        "border: 2px solid #4a5059; border-radius: 8px; "
                                        "padding: 15px;")
        self.value_display.setAlignment(Qt.AlignCenter)
        value_layout.addWidget(self.value_display)
        
        info_layout = QVBoxLayout()
        self.binary_label = QLabel("Binary: 00000000")
        self.binary_label.setFont(QFont("Consolas", 9))
        self.binary_label.setStyleSheet("color: #7dc993;")
        info_layout.addWidget(self.binary_label)
        
        self.hex_label = QLabel("Hex: 0x00")
        self.hex_label.setFont(QFont("Consolas", 9))
        self.hex_label.setStyleSheet("color: #e8b75d;")
        info_layout.addWidget(self.hex_label)
        
        self.duty_label = QLabel("Duty: 0.00%")
        self.duty_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.duty_label.setStyleSheet("color: #9ba5f5;")
        info_layout.addWidget(self.duty_label)
        
        value_layout.addLayout(info_layout)
        layout.addLayout(value_layout)
        
        # Slider
        slider_label = QLabel("LED Intensity Controller (0-100):")
        layout.addWidget(slider_label)
        
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.setValue(0)
        self.slider.setSingleStep(1)
        self.slider.setPageStep(10)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(25)
        self.slider.valueChanged.connect(self.slider_changed)
        layout.addWidget(self.slider)
        
        # Scale markers - properly aligned with slider
        scale_layout = QHBoxLayout()
        scale_layout.setContentsMargins(0, 0, 0, 0)
        scale_layout.setSpacing(0)
        
        # Add left spacing to match slider handle
        scale_layout.addSpacing(9)
        
        labels = [0, 25, 50, 75, 100]
        for i, value in enumerate(labels):
            if i > 0:
                scale_layout.addStretch(1)
            label = QLabel(str(value))
            label.setAlignment(Qt.AlignCenter)
            label.setFixedWidth(18)  # Match slider handle width
            label.setStyleSheet("color: #8a8d94; font-size: 8pt;")
            scale_layout.addWidget(label)
        
        # Add right spacing to match slider handle
        scale_layout.addSpacing(9)
        layout.addLayout(scale_layout)

        
        # Options
        self.auto_send_checkbox = QCheckBox("Auto-send on change")
        self.auto_send_checkbox.setChecked(True)
        layout.addWidget(self.auto_send_checkbox)
        
        # Send button
        self.send_btn = QPushButton("📤 Send Value")
        self.send_btn.clicked.connect(self.send_value)
        self.send_btn.setEnabled(False)
        layout.addWidget(self.send_btn)
        
        # Preset buttons
        preset_layout = QHBoxLayout()
        for value in [0, 25, 50, 100]:
            btn = QPushButton(str(value))
            btn.setMaximumWidth(60)
            btn.clicked.connect(lambda checked, v=value: self.set_preset_value(v))
            preset_layout.addWidget(btn)
        layout.addLayout(preset_layout)
        
        group.setLayout(layout)
        return group
    
    def create_graph_panel(self):
        """Create duty cycle waveform graph panel"""
        group = QGroupBox("📊 Duty Cycle Waveform")
        layout = QVBoxLayout()
        
        # Graph widget
        self.duty_graph = DutyCycleGraph()
        layout.addWidget(self.duty_graph)
        
        # Statistics
        stats_layout = QGridLayout()
        stats_layout.setSpacing(8)
        
        stats_layout.addWidget(QLabel("Period:"), 0, 0)
        self.period_label = QLabel("2.00 µs")
        self.period_label.setStyleSheet("color: #7eb8da; font-weight: bold;")
        stats_layout.addWidget(self.period_label, 0, 1)
        
        stats_layout.addWidget(QLabel("High Time:"), 1, 0)
        self.high_time_label = QLabel("0.00 µs")
        self.high_time_label.setStyleSheet("color: #7dc993; font-weight: bold;")
        stats_layout.addWidget(self.high_time_label, 1, 1)
        
        stats_layout.addWidget(QLabel("Low Time:"), 2, 0)
        self.low_time_label = QLabel("2.00 µs")
        self.low_time_label.setStyleSheet("color: #e8b75d; font-weight: bold;")
        stats_layout.addWidget(self.low_time_label, 2, 1)
        
        layout.addLayout(stats_layout)
        
        group.setLayout(layout)
        return group
    
    def create_monitor_panel(self):
        group = QGroupBox("📊 Activity Monitor")
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        # Statistics
        stats_layout = QHBoxLayout()
        self.sent_count_label = QLabel("Sent: 0")
        self.sent_count_label.setStyleSheet("color: #7dc993; font-weight: bold;")
        stats_layout.addWidget(self.sent_count_label)
        
        self.last_sent_label = QLabel("Last: --")
        stats_layout.addWidget(self.last_sent_label)
        
        stats_layout.addStretch()
        
        self.clear_log_btn = QPushButton("🗑️ Clear")
        self.clear_log_btn.setMaximumWidth(80)
        self.clear_log_btn.clicked.connect(self.clear_log)
        stats_layout.addWidget(self.clear_log_btn)
        
        layout.addLayout(stats_layout)
        
        # Log
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(120)
        layout.addWidget(self.log_text)
        
        group.setLayout(layout)
        return group
    
    def refresh_ports(self):
        """Refresh available COM ports"""
        current_port = self.port_combo.currentText()
        self.port_combo.clear()
        
        ports = serial.tools.list_ports.comports()
        port_list = []
        
        for port in ports:
            port_description = f"{port.device} - {port.description}"
            port_list.append(port_description)
            self.port_combo.addItem(port_description, port.device)
        
        if not port_list:
            self.port_combo.addItem("No ports detected")
            if self.sender() == self.refresh_btn:
                self.log_message("⚠️ No COM ports detected", "#e8b75d")
        else:
            if self.sender() == self.refresh_btn:
                self.log_message(f"✓ Found {len(port_list)} port(s)", "#7dc993")
            
            for i in range(self.port_combo.count()):
                if current_port in self.port_combo.itemText(i):
                    self.port_combo.setCurrentIndex(i)
                    break
    
    def connect_serial(self):
        """Connect to selected serial port"""
        # Get port based on mode
        if self.auto_port_radio.isChecked():
            if self.port_combo.currentIndex() < 0 or self.port_combo.currentText() == "No ports detected":
                self.log_message("❌ No port selected", "#e07b7b")
                return
            port = self.port_combo.currentData()
        else:
            port = self.manual_port_input.text().strip()
            if not port:
                self.log_message("❌ Please enter a port name", "#e07b7b")
                return
        
        baud = int(self.baud_combo.currentText())
        
        databits_map = {5: serial.FIVEBITS, 6: serial.SIXBITS, 
                       7: serial.SEVENBITS, 8: serial.EIGHTBITS}
        databits = databits_map[int(self.databits_combo.currentText())]
        
        parity_map = {"None": serial.PARITY_NONE, "Even": serial.PARITY_EVEN,
                     "Odd": serial.PARITY_ODD}
        parity = parity_map[self.parity_combo.currentText()]
        
        stopbits_map = {"1": serial.STOPBITS_ONE, "2": serial.STOPBITS_TWO}
        stopbits = stopbits_map[self.stopbits_combo.currentText()]
        
        try:
            self.serial_port = serial.Serial(
                port=port,
                baudrate=baud,
                bytesize=databits,
                parity=parity,
                stopbits=stopbits,
                timeout=1
            )
            
            self.log_message(f"✓ Connected to {port} @ {baud} baud", "#7dc993")
            self.statusBar().showMessage(f"Connected to {port}")
            self.status_indicator.setText("● Connected")
            self.status_indicator.setStyleSheet("color: #7dc993; font-weight: bold;")
            
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self.send_btn.setEnabled(True)
            self.auto_port_radio.setEnabled(False)
            self.manual_port_radio.setEnabled(False)
            self.port_combo.setEnabled(False)
            self.manual_port_input.setEnabled(False)
            self.baud_combo.setEnabled(False)
            
            if self.auto_send_checkbox.isChecked():
                self.send_value()
                
        except serial.SerialException as e:
            self.log_message(f"❌ Connection failed: {str(e)}", "#e07b7b")
            self.statusBar().showMessage("Connection failed")
        except Exception as e:
            self.log_message(f"❌ Error: {str(e)}", "#e07b7b")
    
    def disconnect_serial(self):
        """Disconnect from serial port"""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            self.log_message("🔌 Disconnected", "#e8b75d")
            self.statusBar().showMessage("Disconnected")
        
        self.serial_port = None
        self.status_indicator.setText("● Disconnected")
        self.status_indicator.setStyleSheet("color: #e07b7b; font-weight: bold;")
        
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.send_btn.setEnabled(False)
        self.auto_port_radio.setEnabled(True)
        self.manual_port_radio.setEnabled(True)
        self.on_port_mode_changed()  # Re-enable appropriate controls
        self.baud_combo.setEnabled(True)
    
    def slider_changed(self, value):
        """Handle slider value change"""
        self.update_display()
        self.update_duty_cycle_graph()
        
        if self.auto_send_checkbox.isChecked() and self.serial_port and self.serial_port.is_open:
            self.send_value()
    
    def update_display(self):
        """Update value displays"""
        value = self.slider.value()
        self.value_display.setText(str(value))
        
        binary = format(value, '08b')
        hex_val = format(value, '02X')
        
        # Calculate duty cycle percentage (0-100 maps to 0-100%)
        duty_cycle = value
        
        self.binary_label.setText(f"Binary: {binary}")
        self.hex_label.setText(f"Hex: 0x{hex_val}")
        self.duty_label.setText(f"Duty: {duty_cycle:.2f}%")
    
    def update_duty_cycle_graph(self):
        """Update duty cycle waveform and statistics"""
        value = self.slider.value()
        
        # Calculate duty cycle percentage (0-100 maps to 0-100%)
        duty_cycle = value
        
        self.duty_graph.set_duty_cycle(duty_cycle, value)
        
        # Period is 2µs (2000ns)
        period_us = 2.0
        high_time = period_us * duty_cycle / 100
        low_time = period_us - high_time
        
        self.period_label.setText(f"{period_us:.2f} µs")
        self.high_time_label.setText(f"{high_time:.2f} µs")
        self.low_time_label.setText(f"{low_time:.2f} µs")
    
    def send_value(self):
        """Send value to FPGA via UART"""
        if not self.serial_port or not self.serial_port.is_open:
            self.log_message("❌ Not connected", "#e07b7b")
            return
        
        value = self.slider.value()
        
        try:
            self.serial_port.write(bytes([value]))
            
            self.sent_count += 1
            self.sent_count_label.setText(f"Sent: {self.sent_count}")
            
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            self.last_sent_label.setText(f"Last: {timestamp}")
            
            binary = format(value, '08b')
            hex_val = format(value, '02X')
            duty_cycle = (value / 255) * 100
            self.log_message(f"📤 {value} (0b{binary}, 0x{hex_val})", "#7eb8da")
            
        except serial.SerialException as e:
            self.log_message(f"❌ Send failed: {str(e)}", "#e07b7b")
    
    def set_preset_value(self, value):
        """Set slider to preset value"""
        self.slider.setValue(value)
    
    def log_message(self, message, color="#d4d7dc"):
        """Add message to log with color"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted_msg = f'<span style="color: #8a8d94;">[{timestamp}]</span> <span style="color: {color};">{message}</span>'
        self.log_text.append(formatted_msg)
        
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_log(self):
        """Clear activity log"""
        self.log_text.clear()
        self.sent_count = 0
        self.sent_count_label.setText("Sent: 0")
        self.last_sent_label.setText("Last: --")
        self.log_message("📋 Log cleared", "#8a8d94")
    
    def closeEvent(self, event):
        """Handle window close event"""
        self.auto_refresh_timer.stop()
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = FPGAControlGUI()
    window.show()
    sys.exit(app.exec_())