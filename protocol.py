def bytes_to_hex_string(data: bytes) -> str:
    return " ".join(f"{b:02X}" for b in data)


def build_get_position_command() -> bytes:
    """
    CubeMars 문서 기준:
    Get motor position
    02 02 0B 04 9C 7E 03
    """
    return bytes([0x02, 0x02, 0x0B, 0x04, 0x9C, 0x7E, 0x03])


def extract_frames(raw_data: bytes):
    """
    큰 raw_data 안에서 0x02 ... 0x03 형태의 프레임들을 분리한다.
    아주 단순한 프레임 분리기.
    """
    frames = []
    start_idx = None

    for i, b in enumerate(raw_data):
        if b == 0x02 and start_idx is None:
            start_idx = i
        elif b == 0x03 and start_idx is not None:
            frame = raw_data[start_idx:i + 1]
            frames.append(frame)
            start_idx = None

    return frames


def parse_position_response(frame: bytes):
    """
    예상 프레임 형식:
    02 05 16 [4바이트 위치] [2바이트 CRC] 03

    예:
    02 05 16 00 1A B6 64 D5 F4 03
    """

    if len(frame) < 10:
        return False, f"프레임 길이가 너무 짧습니다. len={len(frame)}"

    if frame[0] != 0x02:
        return False, "시작 바이트가 0x02가 아닙니다."

    if frame[-1] != 0x03:
        return False, "끝 바이트가 0x03이 아닙니다."

    length = frame[1]
    frame_id = frame[2]

    if frame_id != 0x16:
        return False, f"frame_id가 0x16이 아닙니다. frame_id=0x{frame_id:02X}"

    # 위치 데이터는 4바이트 signed big-endian
    pos_bytes = frame[3:7]
    pos_int = int.from_bytes(pos_bytes, byteorder="big", signed=True)
    pos_value = pos_int / 10000.0

    return True, {
        "length": length,
        "frame_id": frame_id,
        "position_raw": pos_int,
        "position_value": pos_value,
    }
