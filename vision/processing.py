import cv2
import numpy as np
from fastiecm import fastiecm

class NDVIProcessor:

    @staticmethod
    def contrast_stretch(image: np.ndarray) -> np.ndarray:
        im = np.nan_to_num(image)
        in_min = np.percentile(im, 5)
        in_max = np.percentile(im, 95)
        if abs(in_max - in_min) < 1e-6:
            return np.zeros_like(im, dtype=np.uint8)
        out = (im - in_min) * 255.0 / (in_max - in_min)
        return np.clip(out, 0, 255).astype(np.uint8)

    @staticmethod
    def calculate_ndvi_matrix(image: np.ndarray) -> np.ndarray:
  
        b, _, r = cv2.split(image)
        bottom = r.astype(float) + b.astype(float)
        bottom[bottom == 0] = 1e-18
        return (b.astype(float) - r.astype(float)) / bottom

    @classmethod
    def process_ndvi(cls, raw_frame: np.ndarray) -> np.ndarray:
        contrasted_raw = cls.contrast_stretch(raw_frame)
        ndvi_matrix = cls.calculate_ndvi_matrix(contrasted_raw)
        ndvi_contrasted = cls.contrast_stretch(ndvi_matrix)
        
        # Aplica o mapa de cores especializado Fastie
        color_mapped = cv2.applyColorMap(ndvi_contrasted, fastiecm)
        return color_mapped