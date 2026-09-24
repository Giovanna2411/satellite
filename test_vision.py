import os
import cv2
import numpy as np
from vision import CameraDevice, NDVIProcessor, ImageCompressor, NDVIPipeline

OUTPUT_DIR = "test_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def test_camera_and_processing():
    print("=" * 55)
    print("🔬 [TESTE 1] Testando Câmera e Processamento NDVI")
    print("=" * 55)

    # 1. Teste do CameraDevice
    cam = CameraDevice(width=320, height=240)
    try:
        cam.start()
        raw_frame = cam.capture_frame()
        print(f"Câmera capturou frame com shape: {raw_frame.shape} e tipo {raw_frame.dtype}")
        
        # Salva o frame original bruto
        cv2.imwrite(os.path.join(OUTPUT_DIR, "1_raw_capture.png"), raw_frame)
    finally:
        cam.stop()

    # 2. Teste do NDVIProcessor
    print("\n[TESTE 2] Processamento Matemático do NDVI...")
    processor = NDVIProcessor()
    
    # 2.1 Contraste
    contrasted = processor.contrast_stretch(raw_frame)
    cv2.imwrite(os.path.join(OUTPUT_DIR, "2_contrasted_raw.png"), contrasted)
    print("  └─ Contraste inicial aplicado com sucesso.")

    # 2.2 Matriz NDVI pura
    ndvi_matrix = processor.calculate_ndvi_matrix(contrasted)
    print(f"  └─ NDVI calculado (Min: {np.min(ndvi_matrix):.2f}, Max: {np.max(ndvi_matrix):.2f}, Média: {np.mean(ndvi_matrix):.2f})")

    # 2.3 Mapa de cores Fastie
    ndvi_colored = processor.process_ndvi(raw_frame)
    cv2.imwrite(os.path.join(OUTPUT_DIR, "3_ndvi_fastiecm.png"), ndvi_colored)
    print("  └─ Mapa de cores Fastie aplicado e imagem salva.")

    # 3. Teste do ImageCompressor
    print("\n [TESTE 3] Compressão JPEG...")
    compressor = ImageCompressor(quality=50)
    jpeg_bytes = compressor.to_jpeg(ndvi_colored)
    
    assert jpeg_bytes is not None, "Falha na compressão JPEG"
    tamanho_bytes = len(jpeg_bytes)
    print(f"  └─ Imagem comprimida com sucesso: {tamanho_bytes} bytes (~{tamanho_bytes/1024:.1f} KB)")
    
    with open(os.path.join(OUTPUT_DIR, "4_final_compressed.jpg"), "wb") as f:
        f.write(jpeg_bytes)

def test_full_pipeline():
    print("\n" + "=" * 55)
    print(" [TESTE 4] Testando Pipeline Integrado (NDVIPipeline)")
    print("=" * 55)

    pipe = NDVIPipeline(width=320, height=240, quality=50)
    try:
        pipe.start()
        jpeg_data, t_proc, t_comp = pipe.run()

        print(f" Pipeline executado com sucesso!")
        print(f"  ├─ Tamanho do JPEG : {len(jpeg_data)} bytes")
        print(f"  ├─ Tempo NDVI      : {t_proc * 1000:.2f} ms")
        print(f"  ├─ Tempo Compressão: {t_comp * 1000:.2f} ms")
        print(f"  └─ Tempo Total     : {(t_proc + t_comp) * 1000:.2f} ms")

        # Testa se a imagem JPEG é decodificável
        nparr = np.frombuffer(jpeg_data, np.uint8)
        decoded = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        assert decoded is not None, "A imagem JPEG comprimida pelo pipeline está corrompida"
        print("  └─ Decodificação de verificação: OK (Imagem íntegra)")

    finally:
        pipe.close()

if __name__ == "__main__":
    try:
        test_camera_and_processing()
        test_full_pipeline()
        print("\n TODOS OS TESTES DO PACOTE VISION PASSARAM!")
        print(f"As imagens intermediárias foram salvas na pasta: {OUTPUT_DIR}/\n")
    except Exception as e:
        print(f"\n ERRO NO TESTE: {e}")