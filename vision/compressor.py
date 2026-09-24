import cv2
import numpy as np

class ImageCompressor:
    def __init__(self, quality: int = 50):
        self.quality = quality

    def to_jpeg(self, image: np.ndarray) -> bytes | None:
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, self.quality]
        success, buffer = cv2.imencode(".jpg", image, encode_params)
        if success:
            return buffer.tobytes()
        return None