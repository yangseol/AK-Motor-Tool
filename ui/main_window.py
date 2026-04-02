from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QComboBox,
    QGroupBox,
)

from serial_manager import SerialManager


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.serial_manager = SerialManager()
        self.setWindowTitle("AK70 모터 설정 툴")
        self.resize(700, 500)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        main_layout = QVBoxLayout()

        # 상단: 포트 선택 / 연결
        connection_group = QGroupBox("연결 설정")
        connection_layout = QHBoxLayout()

        port_label = QLabel("포트:")
        self.port_combo = QComboBox()
        self.port_combo.addItem("/dev/ttyUSB0")
        self.port_combo.addItem("/dev/ttyUSB1")
        self.port_combo.addItem("/dev/ttyACM0")

        self.connect_button = QPushButton("연결")
        self.disconnect_button = QPushButton("해제")

        connection_layout.addWidget(port_label)
        connection_layout.addWidget(self.port_combo)
        connection_layout.addWidget(self.connect_button)
        connection_layout.addWidget(self.disconnect_button)
        connection_group.setLayout(connection_layout)

        # 중간: 기능 버튼
        control_group = QGroupBox("기능")
        control_layout = QHBoxLayout()

        self.read_status_button = QPushButton("상태 읽기")
        self.zero_button = QPushButton("현재 위치를 0으로 설정")
        self.calibrate_button = QPushButton("캘리브레이션")

        control_layout.addWidget(self.read_status_button)
        control_layout.addWidget(self.zero_button)
        control_layout.addWidget(self.calibrate_button)
        control_group.setLayout(control_layout)

        # 하단: 로그창
        log_group = QGroupBox("로그")
        log_layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self._append_log("프로그램이 시작되었습니다.")
        self._append_log("UART 연결 기능이 준비되었습니다.")

        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)

        main_layout.addWidget(connection_group)
        main_layout.addWidget(control_group)
        main_layout.addWidget(log_group)

        self.setLayout(main_layout)

    def _connect_signals(self):
        self.connect_button.clicked.connect(self._handle_connect)
        self.disconnect_button.clicked.connect(self._handle_disconnect)

    def _handle_connect(self):
        selected_port = self.port_combo.currentText()
        success, message = self.serial_manager.connect(selected_port)
        self._append_log(message)

    def _handle_disconnect(self):
        success, message = self.serial_manager.disconnect()
        self._append_log(message)

    def _append_log(self, message: str):
        self.log_text.append(message)
