import serial
import serial.tools.list_ports
from PyQt5.QtCore import QThread, pyqtSignal
from dataclasses import dataclass


@dataclass
class SerialConfig:
    port: str
    baudrate: int = 9600
    bytesize: int = 8
    parity: str = 'N'
    stopbits: float = 1
    timeout: float = 1


class SerialReceiver(QThread):
    data_received = pyqtSignal(str)  # 数据接收信号
    error_occurred = pyqtSignal(str)  # 错误发生信号

    def __init__(self, config: SerialConfig, port_index: int):
        super().__init__()
        self.config = config
        self.port_index = port_index
        self.serial_port = None
        self._is_connected = False
        self._should_stop = False

    def run(self):
        """接收数据的线程循环"""
        try:
            self.serial_port = serial.Serial(
                port=self.config.port,
                baudrate=self.config.baudrate,
                bytesize=self.config.bytesize,
                parity=self.config.parity,
                stopbits=self.config.stopbits,
                timeout=self.config.timeout
            )
            self._is_connected = True

            while not self._should_stop and self.serial_port and self.serial_port.is_open:
                try:
                    if self.serial_port.in_waiting > 0:
                        data = self.serial_port.read(self.serial_port.in_waiting)
                        try:
                            text_data = data.decode('utf-8', errors='replace')
                        except:
                            text_data = str(data)
                        self.data_received.emit(text_data)
                except serial.SerialException as e:
                    self.error_occurred.emit(f"串口读取错误: {str(e)}")
                    break

        except serial.SerialException as e:
            error_msg = f"串口连接错误: {str(e)}"
            if "PermissionError" in str(e):
                error_msg = "串口已被占用"
            elif "FileNotFoundError" in str(e):
                error_msg = "串口不存在"
            self.error_occurred.emit(error_msg)
        except Exception as e:
            self.error_occurred.emit(f"未知错误: {str(e)}")
        finally:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
            self._is_connected = False

    def disconnect(self):
        """断开串口连接"""
        self._should_stop = True
        if self.isRunning():
            self.wait(1000)  # 等待线程结束，最多1秒
        self._is_connected = False

    @property
    def is_connected(self):
        return self._is_connected

    @staticmethod
    def get_available_ports() -> list:
        """获取所有可用串口"""
        return [port.device for port in serial.tools.list_ports.comports()]