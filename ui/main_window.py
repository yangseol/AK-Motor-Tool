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
from protocol import make_text_command


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.serial_manager = SerialManager()
        self.setWindowTitle("AK70 모터 설정 툴")
        self.resize(760, 520)
        self._setup_ui()
        self._connect_signals()
        self._refresh_port_list()

    def _setup_ui(self):
        main_layout = QVBoxLayout()

        # 상단: 포트 선택 / 연결
        connection_group = QGroupBox("연결 설정")
        connection_layout = QHBoxLayout()

        port_label = QLabel("포트:")
        self.port_combo = QComboBox()

        self.refresh_button = QPushButton("포트 새로고침")
        self.connect_button = QPushButton("연결")
        self.disconnect_button = QPushButton("해제")

        connection_layout.addWidget(port_label)
        connection_layout.addWidget(self.port_combo)
        connection_layout.addWidget(self.refresh_button)
        connection_layout.addWidget(self.connect_button)
        connection_layout.addWidget(self.disconnect_button)
        connection_group.setLayout(connection_layout)

        # 중간: 기능 버튼
        control_group = QGroupBox("기능")
        control_layout = QHBoxLayout()

        self.read_status_button = QPushButton("상태 읽기")
        self.zero_button = QPushButton("현재 위치를 0으로 설정")
        self.calibrate_button = QPushButton("캘리브레이션")
        self.exit_button = QPushButton("디버그 종료")

        control_layout.addWidget(self.read_status_button)
        control_layout.addWidget(self.zero_button)
        control_layout.addWidget(self.calibrate_button)
        control_layout.addWidget(self.exit_button)
        control_group.setLayout(control_layout)

        # 하단: 로그창
        log_group = QGroupBox("로그")
        log_layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)

        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)

        main_layout.addWidget(connection_group)
        main_layout.addWidget(control_group)
        main_layout.addWidget(log_group)

        self.setLayout(main_layout)

    def _connect_signals(self):
        self.refresh_button.clicked.connect(self._refresh_port_list)
        self.connect_button.clicked.connect(self._handle_connect)
        self.disconnect_button.clicked.connect(self._handle_disconnect)

        self.read_status_button.clicked.connect(self._send_encoder_command)
        self.zero_button.clicked.connect(self._send_zero_command)
        self.calibrate_button.clicked.connect(self._send_calibrate_command)
        self.exit_button.clicked.connect(self._send_exit_command)

    def _refresh_port_list(self):
        self.port_combo.clear()
        ports = self.serial_manager.list_ports()

        if ports:
            self.port_combo.addItems(ports)
            self._append_log("시리얼 포트 목록을 불러왔습니다.")
            for port in ports:
                self._append_log(f"감지된 포트: {port}")
        else:
            self._append_log("감지된 시리얼 포트가 없습니다.")

    def _handle_connect(self):
        if self.port_combo.count() == 0:
            self._append_log("연결할 포트가 없습니다.")
            return

        selected_port = self.port_combo.currentText()
        success, message = self.serial_manager.connect(selected_port)
        self._append_log(message)

    def _handle_disconnect(self):
        success, message = self.serial_manager.disconnect()
        self._append_log(message)

    def _send_encoder_command(self):
        self._send_text_command("encoder", "encoder 명령")

    def _send_calibrate_command(self):
        self._send_text_command("calibrate", "calibrate 명령")

    def _send_exit_command(self):
        self._send_text_command("exit", "exit 명령")

    def _send_zero_command(self):
        self._send_text_command("zero", "zero 명령")

    def _send_text_command(self, command: str, label: str):
        data = make_text_command(command)
        success, message = self.serial_manager.send_bytes(data)
        self._append_log(f"{label} 전송 시도")
        self._append_log(message)

    def _append_log(self, message: str):
        self.log_text.append(message)
