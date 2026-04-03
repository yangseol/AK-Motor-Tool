import time
import serial
import serial.tools.list_ports


class SerialManager:
    def __init__(self):
        self.serial_port = None

    def list_ports(self):
        ports = serial.tools.list_ports.comports()
        filtered_ports = []

        for port in ports:
            device = port.device

            # 내부 기본 포트 제거
            if device.startswith("/dev/ttyS"):
                continue

            filtered_ports.append(device)

        return filtered_ports

    def connect(self, port: str, baudrate: int = 115200, timeout: float = 0.2):
        if self.serial_port and self.serial_port.is_open:
            return True, f"이미 연결되어 있습니다: {self.serial_port.port}"

        try:
            self.serial_port = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=timeout
            )
            return True, f"{port} 연결 성공 (baudrate={baudrate})"
        except Exception as e:
            self.serial_port = None
            return False, f"{port} 연결 실패: {e}"

    def disconnect(self):
        if self.serial_port and self.serial_port.is_open:
            port_name = self.serial_port.port
            self.serial_port.close()
            self.serial_port = None
            return True, f"{port_name} 연결 해제"
        return False, "현재 연결된 포트가 없습니다."

    def is_connected(self):
        return self.serial_port is not None and self.serial_port.is_open

    def send_bytes(self, data: bytes):
        if not self.is_connected():
            return False, "UART가 연결되어 있지 않습니다."

        try:
            self.serial_port.write(data)
            self.serial_port.flush()
            return True, "명령 전송 완료"
        except Exception as e:
            return False, f"명령 전송 실패: {e}"

    def clear_input_buffer(self):
        if self.is_connected():
            try:
                self.serial_port.reset_input_buffer()
            except Exception:
                pass

    def read_packet_once(self, wait_time: float = 0.5, max_bytes: int = 1024):
        if not self.is_connected():
            return False, "UART가 연결되어 있지 않습니다."

        try:
            time.sleep(wait_time)

            available = self.serial_port.in_waiting
            if available <= 0:
                return True, b""

            raw_data = self.serial_port.read(min(available, max_bytes))
            return True, raw_data

        except Exception as e:
            return False, f"응답 읽기 실패: {e}"
