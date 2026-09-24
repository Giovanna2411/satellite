import time
import threading
from datetime import datetime
from comms import E220LoRa, ProtocolManager
from sensors import SensorManager, MPUSensor
from vision.pipeline import NDVIPipeline

lora_lock = threading.Lock()
# Flag global para controlar o tráfego no rádio
transmitindo_imagem = False

def thread_telemetria(lora, protocol, sensors):
    global transmitindo_imagem
    print("[THREAD-TEL] Iniciada com sucesso.")
    while True:
        try:
            # Se a imagem estiver sendo transmitida, a telemetria aguarda para não colidir o canal
            if not transmitindo_imagem:
                sensors_data = sensors.read_all()
                telemetry_frame = protocol.encode_telemetry(sensors_data)
                
                with lora_lock:
                    lora.send_frame(telemetry_frame)
                
                mpu = sensors_data.get("mpu", {})
                accel = mpu.get("accel", {"x": 0, "y": 0, "z": 0})
                gyro = mpu.get("gyro", {"x": 0, "y": 0, "z": 0})
                temp = mpu.get("temp", 0.0)
                timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                print("-" * 50)
                print(f" [TX TELEMETRIA] Nó: {protocol.node_id} | {timestamp_str}")
                print(f"  ├─ Accel (g) : X={accel.get('x'):5.2f} | Y={accel.get('y'):5.2f} | Z={accel.get('z'):5.2f}")
                print(f"  ├─ Gyro (°/s): X={gyro.get('x'):5.2f} | Y={gyro.get('y'):5.2f} | Z={gyro.get('z'):5.2f}")
                print(f"  ├─ Temp      : {temp:.2f} °C")
                print(f"  └─ Sequência : #{protocol.seq}")
                print("-" * 50)
        except Exception as e:
            print(f" [ERRO TELEMETRIA] {e}")
            
        time.sleep(1.0)

def thread_imagens(lora, protocol, ndvi_pipe):
    global transmitindo_imagem
    print("[THREAD-IMG] Iniciada com sucesso.")
    max_payload = 80
    chunk_size = max_payload - 5      
    inter_packet_delay = 0.6          

    time.sleep(5.0)

    while True:
        try:
            photo_id = int(time.time()) % 65535
            timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"\n====================================")
            print(f" [INÍCIO DE CICLO] Foto ID: {photo_id} | {timestamp_str}")
            print(f"====================================")

            # Processa a imagem localmente e salva as etapas
            img_bin, t_proc, t_comp = ndvi_pipe.run_and_save(photo_id)

            if img_bin:
                total_frags = (len(img_bin) + chunk_size - 1) // chunk_size
                
                print("====================================")
                print(f" [TX IMAGEM INICIADA] Foto ID: {photo_id}")
                print(f"  ├─ Resolução : {ndvi_pipe.width}x{ndvi_pipe.height} | Qualidade: {ndvi_pipe.quality}")
                print(f"  ├─ Tamanho   : {len(img_bin)} bytes")
                print(f"  └─ Pacotes   : {total_frags} fragmentos esperados")
                print("====================================")

                # 🛑 BLOQUEIA A TELEMETRIA ANTES DE INICIAR A RAJADA DA IMAGEM
                transmitindo_imagem = True

                # 1. Envia START
                start_frame = protocol.create_image_start(photo_id, total_frags, w=ndvi_pipe.width, h=ndvi_pipe.height, q=ndvi_pipe.quality)
                with lora_lock:
                    lora.send_frame(start_frame)
                time.sleep(0.3)

                # 2. Envia os Fragmentos com o log detalhado de progresso
                for frag_id in range(total_frags):
                    chunk = img_bin[frag_id * chunk_size : (frag_id + 1) * chunk_size]
                    frag_frame = protocol.create_image_fragment(photo_id, frag_id, chunk)
                    
                    with lora_lock:
                        lora.send_frame(frag_frame)
                    
                    current_num = frag_id + 1
                    pct = (current_num / total_frags) * 100.0
                    print(f"  └─ [Foto ID {photo_id}] Enviando pacote {current_num:02d}/{total_frags:02d} ({pct:5.1f}%)")
                    
                    time.sleep(inter_packet_delay)

                # 3. Envia END
                end_frame = protocol.create_image_end(photo_id)
                with lora_lock:
                    lora.send_frame(end_frame)
                
                # LIBERA A TELEMETRIA NOVAMENTE APÓS O FIM DA IMAGEM
                transmitindo_imagem = False
                print("====================================")
                print(f"[TX SUCESSO] Foto ID {photo_id} concluída e transmitida!")
                print(f"  └─ Etapas salvas em: captured_images/")
                print("====================================")
                print("Telemetria liberada.\n")

        except Exception as e:
            transmitindo_imagem = False
            print(f"[ERRO IMAGEM] {e}")

        time.sleep(20.0)

def main():
    print("====================================")
    print("E220 - SATÉLITE MULTITAREFA (THREADS)")
    print("====================================")

    lora = E220LoRa(port="/dev/serial0", baudrate=9600, m0=5, m1=6, aux=25)
    protocol = ProtocolManager(node_id="SAT-01")

    sensors = SensorManager()
    sensors.register("mpu", MPUSensor(bus=1))

    ndvi_pipe = NDVIPipeline(width=320, height=240, quality=50, save_dir="captured_images")

    try:
        print("[SETUP] Inicializando hardware geral...")
        lora.begin(auto_configure=True)
        sensors.setup_all()
        ndvi_pipe.start()
        print("\n [SATÉLITE OPERACIONAL] Disparando Threads...\n")

        # Criação das Threads independentes
        t_tel = threading.Thread(target=thread_telemetria, args=(lora, protocol, sensors), daemon=True)
        t_img = threading.Thread(target=thread_imagens, args=(lora, protocol, ndvi_pipe), daemon=True)

        # Inicia a execução concorrente
        t_tel.start()
        t_img.start()

        # Mantém a thread principal viva esperando interrupção
        while True:
            time.sleep(1.0)

    except KeyboardInterrupt:
        print("\n[TX] Encerrando satélite...")
    finally:
        ndvi_pipe.close()
        lora.close()
        print("[TX] Recursos liberados.")

if __name__ == "__main__":
    main()