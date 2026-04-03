from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QComboBox, QGroupBox, QLineEdit
)
from PyQt5.QtCore import QTimer

from serial_manager import SerialManager
from protocol import (
    build_get_position_command,
    bytes_to_hex_string,
    parse_position_response,
    extract_frames,
)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.serial_manager = SerialManager()
        self.setWindowTitle("AK70 모터 설정 툴")
        self.resize(900, 700)

        # 스트리밍 관련 상태
        self.streaming_enabled = False
        self.latest_position = None

        # 타이머 (100ms)
        self.timer = QTimer()
        self.timer.timeout.connect(self._streaming_step)

        self._setup_ui()
        self._connect_signals()
        self._refresh_port_list()

    def _setup_ui(self):
        main_layout = QVBoxLayout()

        # ===== 연결 =====
        connection_group = QGroupBox("연결 설정")
        connection_layout = QHBoxLayout()

        self.port_combo = QComboBox()
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["115200", "460800", "921600"])
        self.baud_combo.setCurrentText("921600")

        self.refresh_button = QPushButton("포트 새로고침")
        self.connect_button = QPushButton("연결")
        self.disconnect_button = QPushButton("해제")

        connection_layout.addWidget(QLabel("포트:"))
        connection_layout.addWidget(self.port_combo)
        connection_layout.addWidget(QLabel("속도:"))
        connection_layout.addWidget(self.baud_combo)
        connection_layout.addWidget(self.refresh_button)
        connection_layout.addWidget(self.connect_button)
        connection_layout.addWidget(self.disconnect_button)
        connection_group.setLayout(connection_layout)

        # ===== 실시간 표시 =====
        status_group = QGroupBox("실시간 상태")
        status_layout = QHBoxLayout()

        self.position_label = QLabel("현재 위치: --- rad")
        self.position_label.setStyleSheet("font-size: 18px;")

        self.start_stream_button = QPushButton("스트리밍 시작")
        self.stop_stream_button = QPushButton("스트리밍 정지")

        status_layout.addWidget(self.position_label)
        status_layout.addWidget(self.start_stream_button)
        status_layout.addWidget(self.stop_stream_button)
        status_group.setLayout(status_layout)

        # ===== 수동 테스트 =====
        manual_group = QGroupBox("수동 테스트")
        manual_layout = QVBoxLayout()

        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("예: encoder")

        self.hex_input = QLineEdit()
        self.hex_input.setPlaceholderText("예: 02 02 0B 04 9C 7E 03")

        self.send_text_button = QPushButton("문자열 전송")
        self.send_hex_button = QPushButton("HEX 전송")

        manual_layout.addWidget(self.text_input)
        manual_layout.addWidget(self.send_text_button)
        manual_layout.addWidget(self.hex_input)
        manual_layout.addWidget(self.send_hex_button)
        manual_group.setLayout(manual_layout)

        # ===== 로그 =====
        log_group = QGroupBox("로그")
        log_layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)

        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)

        main_layout.addWidget(connection_group)
        main_layout.addWidget(status_group)
        main_layout.addWidget(manual_group)
        main_layout.addWidget(log_group)

        self.setLayout(main_layout)

    def _connect_signals(self):
        self.refresh_button.clicked.connect(self._refresh_port_list)
        self.connect_button.clicked.connect(self._handle_connect)
        self.disconnect_button.clicked.connect(self._handle_disconnect)

        self.start_stream_button.clicked.connect(self._start_streaming)
        self.stop_stream_button.clicked.connect(self._stop_streaming)

        self.send_text_button.clicked.connect(self._handle_send_text)
        self.send_hex_button.clicked.connect(self._handle_send_hex)

    def _refresh_port_list(self):
        self.port_combo.clear()
        ports = self.serial_manager.list_ports()
        if ports:
            self.port_combo.addItems(ports)
            self._append_log("포트 목록 갱신 완료")
        else:
            self._append_log("포트 없음")

    def _handle_connect(self):
        port = self.port_combo.currentText()
        baud = int(self.baud_combo.currentText())
        ok, msg = self.serial_manager.connect(port, baud)
        self._append_log(msg)

    def _handle_disconnect(self):
        ok, msg = self.serial_manager.disconnect()
        self._append_log(msg)

    # ===== 스트리밍 =====
    def _start_streaming(self):
        if not self.serial_manager.is_connected():
            self._append_log("UART 먼저 연결해야 합니다.")
            return

        self.streaming_enabled = True
        self.timer.start(100)
        self._append_log("스트리밍 시작")

    def _stop_streaming(self):
        self.streaming_enabled = False
        self.timer.stop()
        self._append_log("스트리밍 정지")

    def _streaming_step(self):
        if not self.streaming_enabled:
            return

        cmd = build_get_position_command()
        self.serial_manager.clear_input_buffer()
        self.serial_manager.send_bytes(cmd)

        ok, raw = self.serial_manager.read_packet_once(wait_time=0.05)
        if not ok or not raw:
            return

        frames = extract_frames(raw)

        for f in frames:
            ok2, parsed = parse_position_response(f)
            if ok2:
                self.latest_position = parsed["position_value"]

        if self.latest_position is not None:
            self.position_label.setText(
                f"현재 위치: {self.latest_position:.4f} rad"
            )

    # ===== 수동 =====
    def _handle_send_text(self):
        txt = self.text_input.text().strip()
        if not txt:
            return
        data = (txt + "\n").encode()
        self.serial_manager.send_bytes(data)
        self._append_log(f"TX: {txt}")

    def _handle_send_hex(self):
        try:
            data = bytes(int(x, 16) for x in self.hex_input.text().split())
            self.serial_manager.send_bytes(data)
            self._append_log(f"TX HEX: {bytes_to_hex_string(data)}")
        except Exception as e:
            self._append_log(f"HEX 오류: {e}")

    def _append_log(self, msg: str):
        self.log_text.append(msg)
