def make_text_command(command: str) -> bytes:
    """
    UART로 보낼 단순 문자열 명령 생성
    현재는 줄바꿈 포함 텍스트 방식으로 보낸다.
    예: encoder\n, calibrate\n, exit\n
    """
    return (command.strip() + "\n").encode("utf-8")
