import serial
import time
import RPi.GPIO as GPIO

M0 = 5   # Pino Físico 29
M1 = 6   # Pino Físico 31
AUX = 25 # Pino Físico 22

GPIO.setmode(GPIO.BCM)
GPIO.setup(M0, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(M1, GPIO.OUT, initial=GPIO.HIGH)  # M0=0, M1=1 coloca em Configuração
GPIO.setup(AUX, GPIO.IN)

time.sleep(0.1)

print(f"Estado inicial: M0=0, M1=1, AUX={GPIO.input(AUX)}")

try:
    ser = serial.Serial("/dev/serial0", 9600, timeout=1.0)
    ser.reset_input_buffer()

    # Comando C1 00 04: Leitura dos registradores REG0 a REG3
    cmd = b"\xC1\x00\x04"
    print(f"Enviando comando de leitura: {cmd.hex()}")
    ser.write(cmd)
    ser.flush()

    time.sleep(0.15)
    resp = ser.read(10)

    if resp:
        print(f" RESPOSTA RECEBIDA ({len(resp)} bytes): {resp.hex()}")
    else:
        print(" NENHUMA RESPOSTA. O rádio não devolveu bytes.")

except Exception as e:
    print(f"Erro: {e}")
finally:
    GPIO.cleanup()

