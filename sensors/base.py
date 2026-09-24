from abc import ABC, abstractmethod

class BaseSensor(ABC):
    @abstractmethod
    def setup(self) -> None:
        pass

    @abstractmethod
    def read(self) -> dict:
        pass