import time
import serial
try:
    import RPi.GPIO as GPIO
except (ImportError, RuntimeError):
    class GPIOMock:
        BCM = "BCM"
        OUT = "OUT"
        IN = "IN"
        LOW = 0
        HIGH = 1
        @staticmethod
        def setmode(mode): pass
        @staticmethod
        def setup(pin, mode, initial=0): pass
        @staticmethod
        def output(pin, val): pass
        @staticmethod
        def input(pin): return 1
        @staticmethod
        def cleanup(): pass
    GPIO = GPIOMock()

class E220LoRa:
    AIR_RATES = {300: 0, 1200: 1, 2400: 2, 4800: 3, 9600: 4, 19200: 5, 38400: 6, 62500: 7}
    AIR_RATES_REV = {0: 300, 1: 1200, 2: 2400, 3: 4800, 4: 9600, 5: 19200, 6: 38400, 7: 62500}
    TX_POWERS_30D = {0: 30, 1: 27, 2: 24, 3: 21}  # E220-900T30D
    POWER_MAP = {30: 0, 27: 1, 24: 2, 21: 3}
    SUBPACKETS = {200: 0, 128: 1, 64: 2, 32: 3}

    def __init__(self, port="/dev/serial0", baudrate=9600, m0=5, m1=6, aux=25):
        self.port = port
        self.baudrate = baudrate
        self.m0 = m0
        self.m1 = m1
        self.aux = aux
        self.ser = None
        self.hw_config = {}
        self.total_frames_sent = 0
        self.total_bytes_sent = 0
        self.total_aux_wait_time = 0.0

    def begin(self, auto_configure: bool = True):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.m0, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.m1, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.aux, GPIO.IN)

        self.ser = serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1.0
        )
        
        if auto_configure:
            self.configure_radio(
                air_rate=2400,
                tx_power=30,
                freq_mhz=915.125,
                enable_rssi=True,
                subpacket_size=200
            )
        else:
            self.read_hw_config()

        self.set_normal_mode()

    def wait_aux(self, timeout=5.0) -> float:
        inicio = time.monotonic()
        while GPIO.input(self.aux) == GPIO.LOW:
            if time.monotonic() - inicio > timeout:
                raise TimeoutError(f"Timeout de AUX ({timeout}s) - Buffer ou transmissor E220 ocupado.")
            time.sleep(0.001)
        tempo_espera = time.monotonic() - inicio
        time.sleep(0.005)
        return tempo_espera

    def set_normal_mode(self):
        """Normal transmission/reception mode: M0=0, M1=0."""
        GPIO.output(self.m0, GPIO.LOW)
        GPIO.output(self.m1, GPIO.LOW)
        time.sleep(0.05)
        self.wait_aux()
        time.sleep(0.05)

    def set_config_mode(self):
        """Command configuration mode: M0=1, M1=1."""
        GPIO.output(self.m0, GPIO.HIGH)
        GPIO.output(self.m1, GPIO.HIGH)
        time.sleep(0.05)
        self.wait_aux()
        time.sleep(0.05)

    def configure_radio(self, air_rate: int = 2400, tx_power: int = 30, freq_mhz: float = 915.125, enable_rssi: bool = True, subpacket_size: int = 200, temporary: bool = False) -> bool:
        """Configures the E220 LoRa module hardware registers to synchronize RF parameters with the receiver."""
        print("\n[E220 SETUP] Gravando parâmetros de RF no rádio...")
        self.set_config_mode()

        air_rate_val = self.AIR_RATES.get(air_rate, 2)  # 2 = 2400 bps
        reg0 = 0x60 | (air_rate_val & 0x07)

        subpacket_val = self.SUBPACKETS.get(subpacket_size, 0)
        power_val = self.POWER_MAP.get(tx_power, 0)
        reg1 = ((subpacket_val & 0x03) << 6) | (power_val & 0x03)

        # Canal calculado: 915.125 - 850.125 = 65 (0x41)
        canal = int(round(freq_mhz - 850.125))
        canal = max(0, min(80, canal))
        reg2 = canal & 0xFF

        reg3 = (0x80 if enable_rssi else 0x00)

        cmd_header = b"\xC2" if temporary else b"\xC0"
        payload = bytearray([0x00, 0x04, reg0, reg1, reg2, reg3])
        cmd = cmd_header + payload

        self.ser.reset_input_buffer()
        self.ser.write(cmd)
        self.ser.flush()
        
        time.sleep(0.15)
        resposta = self.ser.read(7)

        self.set_normal_mode()

        if len(resposta) >= 3 and resposta[0] in [0xC1, 0xC0, 0xC2]:
            print("[E220 SETUP] Registradores configurados com sucesso!")
            self.read_hw_config()
            return True
        else:
            print("[E220 AVISO] Sem resposta na gravação de registradores.")
            self.read_hw_config()
            return False

    def configure_radio(self, air_rate: int = 2400, tx_power: int = 30, freq_mhz: float = 915.125, enable_rssi: bool = True, subpacket_size: int = 200, temporary: bool = False) -> bool:
        """Writes the 6 configuration registers (ADDH, ADDL, REG0..REG3) to guarantee absolute RF synchronization."""
        print("\n[E220 SETUP] Sincronizando parâmetros de RF no rádio...")
        self.set_config_mode()

        air_rate_val = self.AIR_RATES.get(air_rate, 2)  # 2 = 2400 bps
        reg0 = 0x60 | (air_rate_val & 0x07)            # 0x60 = UART 9600 8N1

        subpacket_val = self.SUBPACKETS.get(subpacket_size, 0)
        power_map = {30: 0, 27: 1, 24: 2, 21: 3}
        power_val = power_map.get(tx_power, 0)
        reg1 = ((subpacket_val & 0x03) << 6) | (power_val & 0x03)

        # Canal calculado: 915.125 - 850.125 = 65 (0x41)
        canal = int(round(freq_mhz - 850.125))
        canal = max(0, min(80, canal))
        reg2 = canal & 0xFF

        # REG3: bit 7 = RSSI (0x80)
        reg3 = 0x80 if enable_rssi else 0x00

        cmd_header = b"\xC2" if temporary else b"\xC0"
        # Grava a partir do endereço 0x00 um total de 6 bytes:
        # [0x00 (ADDH), 0x00 (ADDL), REG0, REG1, REG2 (canal), REG3 (rssi)]
        payload = bytearray([0x00, 0x06, 0x00, 0x00, reg0, reg1, reg2, reg3])
        cmd = cmd_header + payload

        self.ser.reset_input_buffer()
        self.ser.write(cmd)
        self.ser.flush()
        
        time.sleep(0.15)
        resposta = self.ser.read(9)

        self.set_normal_mode()

        if len(resposta) >= 3 and resposta[0] in [0xC1, 0xC0, 0xC2]:
            print("[E220 SETUP] Registradores configurados com sucesso!")
            self.read_hw_config()
            return True
        else:
            print("[E220 AVISO] Sem resposta do E220 na gravação. Verifique conexões UART/M0/M1.")
            self.read_hw_config()
            return False

    def read_hw_config(self) -> dict:
        """Reads the 6 configuration registers starting from address 0x00 to verify the actual hardware state."""
        self.set_config_mode()
        
        self.ser.reset_input_buffer()
        # Comando: C1 (Ler) + Endereço inicial 0x00 + 6 bytes
        self.ser.write(b"\xC1\x00\x06")
        self.ser.flush()
        
        time.sleep(0.15)
        resposta = self.ser.read(9)
        
        self.set_normal_mode()

        if len(resposta) < 9 or resposta[0] != 0xC1:
            print("[HW AVISO] Falha na leitura dos registradores.")
            self.hw_config = {
                "frequencia_mhz": 915.125,
                "air_data_rate_bps": 2400,
                "tx_power_dbm": 30,
                "rssi_enabled": True,
                "status": "FALLBACK"
            }
        else:
            # resposta: [0xC1, 0x00, 0x06, ADDH, ADDL, REG0, REG1, REG2, REG3]
            # Índices:     0     1     2    3     4     5     6     7     8
            reg0 = resposta[5]
            reg1 = resposta[6]
            reg_canal = resposta[7]
            reg3 = resposta[8]

            power_code = reg1 & 0x03
            power_dbm = self.TX_POWERS_30D.get(power_code, 30)

            self.hw_config = {
                "frequencia_mhz": 850.125 + reg_canal * 1.0,
                "air_data_rate_bps": self.AIR_RATES_REV.get(reg0 & 0x07, 2400),
                "tx_power_dbm": power_dbm,
                "rssi_enabled": bool(reg3 & 0x80),
                "subpacket_size": [200, 128, 64, 32][(reg1 >> 6) & 0x03],
                "status": "OK"
            }

        print(f"[HW CONFIRMADO] Frequência: {self.hw_config['frequencia_mhz']:.3f} MHz | Air Rate: {self.hw_config['air_data_rate_bps']} bps | Potência: {self.hw_config['tx_power_dbm']} dBm | Sub-Packet: {self.hw_config.get('subpacket_size', 200)}B | RSSI: {self.hw_config['rssi_enabled']}")
        return self.hw_config

    def send_frame(self, frame_bytes: bytes) -> bool:
        """Envia um frame pronto no ar via UART com controle do pino AUX."""
        if not self.ser or not self.ser.is_open:
            return False
        
        self.wait_aux()
        
        self.ser.write(frame_bytes)
        self.ser.flush()
        
        self.total_frames_sent += 1
        self.total_bytes_sent += len(frame_bytes)
        return True

    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
        GPIO.cleanup()