import json
import time
import struct
from .framing import make_frame

class PacketType:
    TELEMETRY = "T"
    IMAGE_START = "S"
    IMAGE_FRAG = "F"
    IMAGE_END = "E"
    UNKNOWN = "U"

class TelemetryProtocol:
    @staticmethod
    def identify_type(packet_bytes: bytes) -> str:
        if not packet_bytes:
            return PacketType.UNKNOWN
        header_char = chr(packet_bytes[0])
        if header_char in ["T", "S", "F", "E"]:
            return header_char
        return PacketType.UNKNOWN

    @staticmethod
    def decode_telemetry(packet_bytes: bytes) -> dict | None:
        try:
            raw_json = packet_bytes[1:].decode('utf-8')
            return json.loads(raw_json)
        except Exception:
            return None

class ProtocolManager:
    def __init__(self, node_id="SAT-01"):
        self.node_id = node_id
        self.seq = 0

    def encode_telemetry(self, sensors_data: dict) -> bytes:
        self.seq += 1

        packet = {
            "node": self.node_id,
            "seq": self.seq,
            "time": int(time.time()),
            **sensors_data
        }

        json_bytes = json.dumps(packet, separators=(',', ':')).encode('utf-8')
        raw_packet = b"T" + json_bytes
        return make_frame(raw_packet)

    @staticmethod
    def create_image_start(photo_id: int, total_frags: int, w: int, h: int, q: int) -> bytes:
        payload = struct.pack("!BHHHHB", ord("S"), photo_id, total_frags, w, h, q)
        return make_frame(payload)

    @staticmethod
    def create_image_fragment(photo_id: int, frag_id: int, chunk: bytes) -> bytes:
        header = struct.pack("!BHH", ord("F"), photo_id, frag_id)
        return make_frame(header + chunk)

    @staticmethod
    def create_image_end(photo_id: int) -> bytes:
        payload = struct.pack("!BH", ord("E"), photo_id)
        return make_frame(payload)