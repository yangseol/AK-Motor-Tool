import serial
import serial.tools.list_ports


class SerialManager:
    def __init__(self):
        self.serial_port = None

    def list_ports(self):
        """
        실제 USB 시리얼 장치로 보이는 포트만 반환
        예: /dev/ttyUSB0, /dev/ttyACM0
        내부 포트(/dev/ttyS0 등)는 제외
        """
        ports = serial.tools.list_ports.comports()
        filtered_ports = []

        for port in ports:
            device = port.device
            if "ttyUSB" in device or "ttyACM" in device:
                filtered_ports.append(device)

        return filtered_ports

    def connect(self, port: str, baudrate: int = 115200, timeout: float = 0.1):
        if self.serial_port and self.serial_port.is_open:
            return True, f"이미 연결되어 있습니다: {self.serial_port.port}"

        try:
            self.serial_port = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=timeout
            )
            return True, f"{port} 연결 성공"
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
            return True, f"명령 전송 완료: {data!r}"
        except Exception as e:
            return False, f"명령 전송 실패: {e}"
