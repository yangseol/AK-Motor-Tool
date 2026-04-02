def bytes_to_hex_string(data: bytes) -> str:
    return " ".join(f"{b:02X}" for b in data)


def build_get_position_command() -> bytes:
    """
    CubeMars 문서 기준:
    Get motor position
    Command:
    02 02 0B 04 9C 7E 03
    """
    return bytes([0x02, 0x02, 0x0B, 0x04, 0x9C, 0x7E, 0x03])


def parse_position_response(raw_data: bytes):
    """
    예시 응답:
    02 05 16 00 1A B6 64 D5 F4 03

    기본 검증만 수행하고,
    4바이트 위치값을 추출해서 float로 환산한다.
    """
    if len(raw_data) < 10:
        return False, "응답 길이가 너무 짧습니다."

    if raw_data[0] != 0x02:
        return False, "응답 시작 바이트(0x02)가 아닙니다."

    if raw_data[-1] != 0x03:
        return False, "응답 끝 바이트(0x03)가 아닙니다."

    data_length = raw_data[1]
    frame_id = raw_data[2]

    if frame_id != 0x16:
        return False, f"예상한 응답 프레임(0x16)이 아닙니다. frame_id=0x{frame_id:02X}"

    # 응답 포맷:
    # [0] 0x02
    # [1] length
    # [2] frame_id
    # [3:7] 4-byte position
    # [7:9] CRC
    # [9] 0x03
    pos_bytes = raw_data[3:7]
    pos_int = int.from_bytes(pos_bytes, byteorder="big", signed=True)
    pos_value = pos_int / 10000.0

    return True, {
        "length": data_length,
        "frame_id": frame_id,
        "position_raw": pos_int,
        "position_value": pos_value,
    }
