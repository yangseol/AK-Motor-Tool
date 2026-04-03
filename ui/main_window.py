from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QComboBox,
    QGroupBox,
    QLineEdit,
)

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
        self.resize(900, 650)
        self._setup_ui()
        self._connect_signals()
        self._refresh_port_list()

    def _setup_ui(self):
        main_layout = QVBoxLayout()

        connection_group = QGroupBox("연결 설정")
        connection_layout = QHBoxLayout()

        port_label = QLabel("포트:")
        self.port_combo = QComboBox()

        baud_label = QLabel("속도:")
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["115200", "460800", "921600"])
        self.baud_combo.setCurrentText("115200")

        self.refresh_button = QPushButton("포트 새로고침")
        self.connect_button = QPushButton("연결")
        self.disconnect_button = QPushButton("해제")

        connection_layout.addWidget(port_label)
        connection_layout.addWidget(self.port_combo)
        connection_layout.addWidget(baud_label)
        connection_layout.addWidget(self.baud_combo)
        connection_layout.addWidget(self.refresh_button)
        connection_layout.addWidget(self.connect_button)
        connection_layout.addWidget(self.disconnect_button)
        connection_group.setLayout(connection_layout)

        control_group = QGroupBox("기본 기능")
        control_layout = QHBoxLayout()

        self.read_status_button = QPushButton("위치 읽기")
        self.zero_button = QPushButton("현재 위치를 0으로 설정")
        self.calibrate_button = QPushButton("캘리브레이션")
        self.exit_button = QPushButton("디버그 종료")

        control_layout.addWidget(self.read_status_button)
        control_layout.addWidget(self.zero_button)
        control_layout.addWidget(self.calibrate_button)
        control_layout.addWidget(self.exit_button)
        control_group.setLayout(control_layout)

        manual_group = QGroupBox("수동 테스트")
        manual_layout = QVBoxLayout()

        text_layout = QHBoxLayout()
        text_label = QLabel("문자열 명령:")
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("예: encoder 또는 calibrate")
        self.send_text_button = QPushButton("문자열 전송")

        text_layout.addWidget(text_label)
        text_layout.addWidget(self.text_input)
        text_layout.addWidget(self.send_text_button)

        hex_layout = QHBoxLayout()
        hex_label = QLabel("HEX 명령:")
        self.hex_input = QLineEdit()
        self.hex_input.setPlaceholderText("예: 02 02 0B 04 9C 7E 03")
        self.send_hex_button = QPushButton("HEX 전송")

        hex_layout.addWidget(hex_label)
        hex_layout.addWidget(self.hex_input)
        hex_layout.addWidget(self.send_hex_button)

        manual_layout.addLayout(text_layout)
        manual_layout.addLayout(hex_layout)
        manual_group.setLayout(manual_layout)

        log_group = QGroupBox("로그")
        log_layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)

        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)

        main_layout.addWidget(connection_group)
        main_layout.addWidget(control_group)
        main_layout.addWidget(manual_group)
        main_layout.addWidget(log_group)

        self.setLayout(main_layout)

    def _connect_signals(self):
        self.refresh_button.clicked.connect(self._refresh_port_list)
        self.connect_button.clicked.connect(self._handle_connect)
        self.disconnect_button.clicked.connect(self._handle_disconnect)

        self.read_status_button.clicked.connect(self._handle_read_position)
        self.zero_button.clicked.connect(self._handle_not_implemented)
        self.calibrate_button.clicked.connect(self._handle_not_implemented)
        self.exit_button.clicked.connect(self._handle_not_implemented)

        self.send_text_button.clicked.connect(self._handle_send_text)
        self.send_hex_button.clicked.connect(self._handle_send_hex)

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
        selected_baud = int(self.baud_combo.currentText())

        success, message = self.serial_manager.connect(selected_port, baudrate=selected_baud)
        self._append_log(message)

    def _handle_disconnect(self):
        success, message = self.serial_manager.disconnect()
        self._append_log(message)

    def _handle_read_position(self):
        self._append_log("위치 조회 패킷 전송 시도")

        command = build_get_position_command()
        self._append_log(f"송신 HEX: {bytes_to_hex_string(command)}")

        self.serial_manager.clear_input_buffer()

        success, message = self.serial_manager.send_bytes(command)
        self._append_log(message)

        if not success:
            return

        self._read_and_print_response(parse_position=True)

    def _handle_send_text(self):
        text = self.text_input.text().strip()
        if not text:
            self._append_log("문자열 명령이 비어 있습니다.")
            return

        data = (text + "\n").encode("utf-8")
        self._append_log(f"문자열 전송 시도: {text}")
        self._append_log(f"송신 HEX: {bytes_to_hex_string(data)}")

        self.serial_manager.clear_input_buffer()

        success, message = self.serial_manager.send_bytes(data)
        self._append_log(message)

        if not success:
            return

        self._read_and_print_response(parse_position=False)

    def _handle_send_hex(self):
        hex_text = self.hex_input.text().strip()
        if not hex_text:
            self._append_log("HEX 명령이 비어 있습니다.")
            return

        try:
            parts = hex_text.split()
            data = bytes(int(part, 16) for part in parts)
        except Exception as e:
            self._append_log(f"HEX 변환 실패: {e}")
            return

        self._append_log(f"HEX 전송 시도: {hex_text}")
        self._append_log(f"송신 HEX: {bytes_to_hex_string(data)}")

        self.serial_manager.clear_input_buffer()

        success, message = self.serial_manager.send_bytes(data)
        self._append_log(message)

        if not success:
            return

        self._read_and_print_response(parse_position=False)

    def _read_and_print_response(self, parse_position: bool):
        read_success, raw_data = self.serial_manager.read_packet_once(wait_time=0.6)

        if not read_success:
            self._append_log(f"수신 실패: {raw_data}")
            return

        if not raw_data:
            self._append_log("수신된 응답이 없습니다.")
            return

        self._append_log(f"수신 HEX RAW: {bytes_to_hex_string(raw_data)}")

        frames = extract_frames(raw_data)
        self._append_log(f"분리된 프레임 수: {len(frames)}")

        if not frames:
            self._append_log("유효한 0x02~0x03 프레임을 찾지 못했습니다.")
            return

        for idx, frame in enumerate(frames, start=1):
            self._append_log(f"[프레임 {idx}] {bytes_to_hex_string(frame)}")

            if parse_position:
                parsed_ok, parsed_result = parse_position_response(frame)

                if parsed_ok:
                    self._append_log(
                        f"  위치 raw={parsed_result['position_raw']}, "
                        f"위치 값={parsed_result['position_value']:.4f}"
                    )
                else:
                    self._append_log(f"  파싱 실패: {parsed_result}")

    def _handle_not_implemented(self):
        self._append_log("이 기능은 다음 단계에서 구현합니다.")

    def _append_log(self, message: str):
        self.log_text.append(message)
