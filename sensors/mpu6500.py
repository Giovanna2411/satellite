from sensors.base import BaseSensor
from mpu9250_jmdev.mpu_9250 import MPU9250
from mpu9250_jmdev.registers import (
    AK8963_ADDRESS,
    AK8963_MODE_C100HZ,
    AK8963_BIT_16,
    MPU9050_ADDRESS_68,
    GFS_250,
    AFS_2G,
)

class MPUSensor(BaseSensor):
    def __init__(self, bus=1):
        self.bus = bus
        self.mpu = None

    def setup(self):
        self.mpu = MPU9250(
            address_ak=AK8963_ADDRESS,
            address_mpu_master=MPU9050_ADDRESS_68,
            address_mpu_slave=None,
            bus=self.bus,
            gfs=GFS_250,
            afs=AFS_2G,
            mfs=AK8963_BIT_16,
            mode=AK8963_MODE_C100HZ
        )
        
        self.mpu.configure()
        print("[Sensor MPU] Configurado com sucesso!")

    def read(self) -> dict:
        accel = self.mpu.readAccelerometerMaster()
        gyro = self.mpu.readGyroscopeMaster()
        temp = self.mpu.readTemperatureMaster()
        
        return {
            "accel": {
                "x": round(accel[0], 2),
                "y": round(accel[1], 2),
                "z": round(accel[2], 2)
            },
            "gyro": {
                "x": round(gyro[0], 2),
                "y": round(gyro[1], 2),
                "z": round(gyro[2], 2)
            },
            "temp": round(temp, 2)
        }