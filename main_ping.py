import time
from comms import E220LoRa, ProtocolManager

def main():
    print("====================================")
    print("E220 - TRANSMISSOR DE PING (ALCANCE)")
    print("====================================")

    # 1. Inicializa o rádio usando a classe oficial do projeto
    lora = E220LoRa(port="/dev/serial0", baudrate=9600, m0=5, m1=6, aux=25)
    
    # 2. Inicializa o gerenciador de protocolo para empacotar os dados
    protocol = ProtocolManager(node_id="PING-TX")

    try:
        print("[SETUP] Inicializando rádio transmissor...")
        # Configura automaticamente os registradores em 915.125 MHz, 2400 bps com RSSI
        lora.begin(auto_configure=True)
        print("\n[TRANSMISSOR PING ATIVO] Iniciando disparos de teste...\n")
        print("-" * 50)

        contador = 1

        while True:
 
            dados_ping = {
                "node": protocol.node_id,
                "seq": contador,
                "time": int(time.time()),
                "msg": "PING_TESTE_ALCANCE"
            }

            # 2. Converte para o formato de string JSON que simula o pacote 'T'
            import json
            payload_str = json.dumps(dados_ping)
            conteudo_exibicao = f"T{payload_str}"

            # 3. Cria o frame binário real com o ProtocolManager (com MAGIC e CRC)
            tx_frame = protocol.encode_telemetry(dados_ping)

            # 4. Exibe no console exatamente o que o receptor vai ler
            print(f"[ENVIANDO PING #{contador}] ({len(tx_frame)} bytes no ar)")
            print(f"   Conteúdo: {conteudo_exibicao}")
            print("-" * 50)
            
            # 5. Envia pelo rádio
            lora.send_frame(tx_frame)

            contador += 1
            if contador > 9999:
                contador = 1

            time.sleep(2.0)

    except KeyboardInterrupt:
        print("\n[TX] Encerrando transmissor de PING...")
    finally:
        lora.close()
        print("[TX] Recursos liberados.")

if __name__ == "__main__":
    main()