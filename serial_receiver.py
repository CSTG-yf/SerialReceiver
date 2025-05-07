import serial
import serial.tools.list_ports
import threading
from dataclasses import dataclass
from typing import Callable, Optional

@dataclass
class SerialConfig:
    port: str
    baudrate: int = 9600
    bytesize: int = 8
    parity: str = 'N'
    stopbits: float = 1
    timeout: float = 1

class SerialReceiver:
    def __init__(self, data_received_callback: Callable[[str], None]):
        self.serial_port = None
        self.is_connected = False
        self.receive_thread = None
        self.should_stop = False
        self.data_received_callback = data_received_callback

    def get_available_ports(self) -> list[str]:
        """获取所有可用串口"""
        return [port.device for port in serial.tools.list_ports.comports()]

    def connect(self, config: SerialConfig) -> bool:
        """连接串口"""
        if self.is_connected:
            return False

        try:
            self.serial_port = serial.Serial(
                port=config.port,
                baudrate=config.baudrate,
                bytesize=config.bytesize,
                parity=config.parity,
                stopbits=config.stopbits,
                timeout=config.timeout
            )
            self.is_connected = True
            self.should_stop = False
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False

    def disconnect(self):
        """断开串口连接"""
        if not self.is_connected:
            return

        self.should_stop = True
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=1)

        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()

        self.is_connected = False

    def _receive_loop(self):
        """接收数据的循环"""
        while not self.should_stop and self.serial_port and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting > 0:
                    data = self.serial_port.read(self.serial_port.in_waiting)
                    try:
                        text_data = data.decode('utf-8', errors='replace')
                    except:
                        text_data = str(data)
                    self.data_received_callback(text_data)
            except Exception as e:
                self.data_received_callback(f"\nReceive error: {e}\n")
                break