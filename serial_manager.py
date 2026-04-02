import serial


class SerialManager:
    def __init__(self):
        self.serial_port = None

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
