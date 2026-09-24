import os
import time
import cv2
import numpy as np
from fastiecm import fastiecm

from vision.camera import CameraDevice
from vision.processing import NDVIProcessor
from vision.compressor import ImageCompressor

class NDVIPipeline:
    def __init__(self, width: int = 320, height: int = 240, quality: int = 50, save_dir: str = "captured_images"):
        self.width = width
        self.height = height
        self.quality = quality
        self.save_dir = save_dir
        
        self.camera = CameraDevice(width=width, height=height)
        self.processor = NDVIProcessor()
        self.compressor = ImageCompressor(quality=quality)

    def start(self):
        self.camera.start()

    def run_and_save(self, photo_id: int) -> tuple[bytes | None, float, float]:

        os.makedirs(self.save_dir, exist_ok=True)
        
        # 1. Captura Original
        t0 = time.perf_counter()
        raw_frame = self.camera.capture_frame()  # Corrigido de capture_array para capture_frame
        
        # Salva etapa 1: Original
        path_orig = os.path.join(self.save_dir, f"foto_{photo_id}_1_original.png")
        cv2.imwrite(path_orig, raw_frame)

        # 2. Processamento Científico (Contraste e NDVI)
        contrasted_raw = self.processor.contrast_stretch(raw_frame)
        path_cont = os.path.join(self.save_dir, f"foto_{photo_id}_2_contrasted.png")
        cv2.imwrite(path_cont, contrasted_raw)

        ndvi_matrix = self.processor.calculate_ndvi_matrix(contrasted_raw)
        ndvi_contrasted = self.processor.contrast_stretch(ndvi_matrix)
        path_ndvi = os.path.join(self.save_dir, f"foto_{photo_id}_3_ndvi_contrasted.png")
        cv2.imwrite(path_ndvi, ndvi_contrasted)

        # Mapa de cores FastieCM
        color_mapped_prep = ndvi_contrasted.astype(np.uint8)
        color_mapped_image = cv2.applyColorMap(color_mapped_prep, fastiecm if 'fastiecm' in globals() else cv2.COLORMAP_JET) # Mantém o fastiecm do seu processing
        
        path_map = os.path.join(self.save_dir, f"foto_{photo_id}_4_color_mapped.png")
        cv2.imwrite(path_map, color_mapped_image)
        t_proc = time.perf_counter() - t0

        # 3. Compressão JPEG da imagem color_mapped final para transmissão
        t1 = time.perf_counter()
        jpeg_bytes = self.compressor.to_jpeg(color_mapped_image)
        t_comp = time.perf_counter() - t1

        # Salva o JPEG final comprimido na pasta local também
        path_jpg = os.path.join(self.save_dir, f"foto_{photo_id}_final.jpg")
        if jpeg_bytes:
            with open(path_jpg, "wb") as f:
                f.write(jpeg_bytes)

        return jpeg_bytes, t_proc, t_comp

    def close(self):
        self.camera.stop()