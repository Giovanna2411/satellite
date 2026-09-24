import time
from picamera2 import Picamera2

class CameraDevice:
    def __init__(self, width: int = 320, height: int = 240):
        self.width = width
        self.height = height
        self._cam = None

    def start(self):
        print(f"[CÂMERA] Inicializando sensor ({self.width}x{self.height})...")
        self._cam = Picamera2()
        config = self._cam.create_still_configuration(
            main={"size": (self.width, self.height)}
        )
        self._cam.configure(config)
        self._cam.start()
        time.sleep(2.0) 
        print("[CÂMERA] Pronta.")

    def capture_frame(self):
        if self._cam is None:
            raise RuntimeError("Câmera não foi inicializada. Chame start() primeiro.")
        return self._cam.capture_array()

    def stop(self):
        if self._cam is not None:
            try:
                self._cam.stop()
            except Exception:
                pass
            try:
                self._cam.close()  
            except Exception:
                pass
            self._cam = None
            print("[CÂMERA] Encerrada e liberada.")