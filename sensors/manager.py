from typing import Dict
from sensors.base import BaseSensor

class SensorManager:
    def __init__(self):
        self._sensors: Dict[str, BaseSensor] = {}

    def register(self, name: str, sensor: BaseSensor):
        self._sensors[name] = sensor

    def setup_all(self):
        for name, sensor in self._sensors.items():
            print(f"[Sensors] Inicializando {name}...")
            sensor.setup()

    def read_all(self) -> dict:
        data = {}
        for name, sensor in self._sensors.items():
            try:
                data[name] = sensor.read()
            except Exception as e:
                data[name] = {"error": str(e)}
        return data