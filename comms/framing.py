import struct

MAGIC = b"\xAA\x55"
MAX_FRAME_SIZE = 512 

def crc16(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc

def make_frame(packet_data: bytes) -> bytes:
    if len(packet_data) > (MAX_FRAME_SIZE - 6):
        raise ValueError(f"Payload excede o limite: {len(packet_data)} bytes")
    tamanho = len(packet_data)
    crc = crc16(packet_data)
    
    return MAGIC + struct.pack("!H", tamanho) + packet_data + struct.pack("!H", crc)

class FrameDecoder:
    def __init__(self):
        self.buffer = bytearray()
        self.valid_frames = 0
        self.crc_errors = 0
        self.sync_losses = 0

    def feed_and_extract(self, raw_bytes: bytes) -> tuple[bytes | None, int | None]:
        # Se foram recebidos novos bytes na UART, anexa-os ao final do buffer de processamento
        if raw_bytes:
            self.buffer.extend(raw_bytes)

        pos = self.buffer.find(MAGIC)
        if pos == -1:

        
            if len(self.buffer) > 1:
                self.buffer = self.buffer[-1:]
            return None, None

        if pos > 0:
            self.sync_losses += 1
            del self.buffer[:pos]

        if len(self.buffer) < 4:
            return None, None

        tamanho = struct.unpack("!H", self.buffer[2:4])[0]
        if tamanho == 0 or tamanho > (MAX_FRAME_SIZE - 6):
            del self.buffer[:2]
            return None, None

        frame_size = 2 + 2 + tamanho + 2
        if len(self.buffer) < frame_size:
            return None, None

        packet_data = bytes(self.buffer[4:4 + tamanho])
        crc_recebido = struct.unpack("!H", self.buffer[4 + tamanho:6 + tamanho])[0]
        crc_calculado = crc16(packet_data)

        if crc_recebido != crc_calculado:
            self.crc_errors += 1
            print(f"[CRC ERRO] Corrupção: Recebido 0x{crc_recebido:04X} != Calculado 0x{crc_calculado:04X}")
            del self.buffer[:2]
            return None, None

        rssi_dbm = None
        bytes_to_consume = frame_size
        if len(self.buffer) > frame_size:
            if len(self.buffer) == frame_size + 1 or self.buffer[frame_size:frame_size+2] != MAGIC:
                rssi_raw = self.buffer[frame_size]
                rssi_dbm = -(256 - rssi_raw) if rssi_raw > 0 else 0 
                bytes_to_consume = frame_size + 1

        del self.buffer[:bytes_to_consume]
        self.valid_frames += 1
        return packet_data, rssi_dbm