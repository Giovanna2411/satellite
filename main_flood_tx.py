import time
from comms import E220LoRa, ProtocolManager

def main():
    print("====================================")
    print("E220 - TRANSMISSOR DE FLOOD / CARGA")
    print("====================================")

    # 1. Inicializa rádio e protocolo oficiais
    lora = E220LoRa(port="/dev/serial0", baudrate=9600, m0=5, m1=6, aux=25)
    protocol = ProtocolManager(node_id="FLOOD-TX")

    max_payload = 80
    chunk_size = max_payload - 5      # 75 bytes úteis por fragmento
    inter_packet_delay = 0.6          

    try:
        print("[SETUP] Inicializando rádio transmissor...")
        lora.begin(auto_configure=True)
        print("\n[TRANSMISSOR FLOOD ATIVO] Sincronizado com o perfil de imagem...\n")
        print("-" * 50)

        photo_id = 123

        while True:
            # Dados simulados (5000 bytes)
            data = bytes([1] * 5000)
            total_frags = (len(data) + chunk_size - 1) // chunk_size

            print(f"\n====================================")
            print(f"NOVA TRANSMISSÃO DE CARGA (ID: {photo_id})")
            print(f"====================================")
            print(f"Bytes totais: {len(data)} | Chunk: {chunk_size} | Total de fragmentos: {total_frags}")

            # --------------------------------------------------------
            # 1. Envia START ('S') exatamente como na imagem
            # --------------------------------------------------------
            start_frame = protocol.create_image_start(photo_id, total_frags, w=320, h=240, q=50)
            lora.send_frame(start_frame)
            time.sleep(0.3)

            # --------------------------------------------------------
            # 2. Envia os FRAGMENTOS ('F') com o mesmo padrão da imagem
            # --------------------------------------------------------
            for frag_id in range(total_frags):
                chunk = data[frag_id * chunk_size : (frag_id + 1) * chunk_size]
                frag_frame = protocol.create_image_fragment(photo_id, frag_id, chunk)
                
                lora.send_frame(frag_frame)
                
                current_num = frag_id + 1
                pct = (current_num / total_frags) * 100.0
                print(f"  └─ [Carga ID {photo_id}] Enviando pacote {current_num:02d}/{total_frags:02d} ({pct:5.1f}%)")
                time.sleep(inter_packet_delay)

            # --------------------------------------------------------
            # 3. Envia END ('E') exatamente como na imagem
            # --------------------------------------------------------
            end_frame = protocol.create_image_end(photo_id)
            lora.send_frame(end_frame)
            
            print("Ciclo de transmissão de carga concluído com sucesso.")
            print("-" * 50)

            photo_id += 1
            if photo_id > 65535:
                photo_id = 100

            time.sleep(5.0)

    except KeyboardInterrupt:
        print("\n[TX] Encerrando transmissor de flood...")
    finally:
        lora.close()
        print("[TX] Recursos liberados.")

if __name__ == "__main__":
    main()
