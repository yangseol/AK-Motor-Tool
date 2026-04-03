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
        self.resize(900, 720)

        # 스트리밍 관련 상태
        self.streaming_enabled = False
        self.latest_position = None
        self.zero_offset = 0.0
        self.zero_set = False

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
        status_layout = QVBoxLayout()

        label_row_1 = QHBoxLayout()
        self.raw_position_label = QLabel("실제 위치: --- rad")
        self.raw_position_label.setStyleSheet("font-size: 18px;")
        label_row_1.addWidget(self.raw_position_label)

        label_row_2 = QHBoxLayout()
        self.relative_position_label = QLabel("보정 위치: --- rad")
        self.relative_position_label.setStyleSheet("font-size: 18px;")
        label_row_2.addWidget(self.relative_position_label)

        button_row = QHBoxLayout()
        self.start_stream_button = QPushButton("스트리밍 시작")
        self.stop_stream_button = QPushButton("스트리밍 정지")
        self.zero_button = QPushButton("현재 위치를 0으로 설정")
        self.clear_zero_button = QPushButton("0 설정 해제")

        button_row.addWidget(self.start_stream_button)
        button_row.addWidget(self.stop_stream_button)
        button_row.addWidget(self.zero_button)
        button_row.addWidget(self.clear_zero_button)

        status_layout.addLayout(label_row_1)
        status_layout.addLayout(label_row_2)
        status_layout.addLayout(button_row)
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
        self.calibrate_button = QPushButton("캘리브레이션 (미구현)")
        self.exit_button = QPushButton("디버그 종료 (미구현)")

        manual_layout.addWidget(self.text_input)
        manual_layout.addWidget(self.send_text_button)
        manual_layout.addWidget(self.hex_input)
        manual_layout.addWidget(self.send_hex_button)
        manual_layout.addWidget(self.calibrate_button)
        manual_layout.addWidget(self.exit_button)
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
        self.zero_button.clicked.connect(self._set_zero_here)
        self.clear_zero_button.clicked.connect(self._clear_zero)

        self.send_text_button.clicked.connect(self._handle_send_text)
        self.send_hex_button.clicked.connect(self._handle_send_hex)
        self.calibrate_button.clicked.connect(self._handle_not_implemented)
        self.exit_button.clicked.connect(self._handle_not_implemented)

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

        for frame in frames:
            parsed_ok, parsed = parse_position_response(frame)
            if parsed_ok:
                self.latest_position = parsed["position_value"]

        if self.latest_position is not None:
            self.raw_position_label.setText(
                f"실제 위치: {self.latest_position:.4f} rad"
            )

            if self.zero_set:
                relative = self.latest_position - self.zero_offset
                self.relative_position_label.setText(
                    f"보정 위치: {relative:.4f} rad"
                )
            else:
                self.relative_position_label.setText(
                    f"보정 위치: {self.latest_position:.4f} rad"
                )

    def _set_zero_here(self):
        if self.latest_position is None:
            self._append_log("아직 위치값이 없습니다. 먼저 스트리밍을 시작하세요.")
            return

        self.zero_offset = self.latest_position
        self.zero_set = True
        self._append_log(f"현재 위치를 0 기준으로 설정: offset={self.zero_offset:.4f} rad")

    def _clear_zero(self):
        self.zero_offset = 0.0
        self.zero_set = False
        self._append_log("0 기준 설정 해제")

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

    def _handle_not_implemented(self):
        self._append_log("이 기능은 다음 단계에서 구현합니다.")

    def _append_log(self, msg: str):
        self.log_text.append(msg)
