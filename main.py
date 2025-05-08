import serial
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QComboBox, QPushButton, QTextEdit, QGroupBox, QScrollArea, QFileDialog,
                             QMessageBox, QFrame, QGridLayout, QSizePolicy)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor
from serial_receiver import SerialReceiver, SerialConfig
import sys


class SerialPortWidget(QGroupBox):
    """单个串口控件"""

    def __init__(self, port_index: int, parent=None):
        super().__init__(f"串口 {port_index + 1}", parent)
        self.port_index = port_index
        self.serial_receiver = None
        self.is_receiving = True  # 默认接收数据

        # 创建UI
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        # 配置区域
        config_layout = QHBoxLayout()
        config_layout.setSpacing(6)

        self.port_combo = QComboBox()
        self.port_combo.setFixedWidth(150)
        config_layout.addWidget(self.port_combo)

        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems(['9600', '19200', '38400', '57600', '115200'])
        self.baudrate_combo.setCurrentText('9600')
        self.baudrate_combo.setFixedWidth(100)
        config_layout.addWidget(self.baudrate_combo)

        self.connect_btn = QPushButton("连接")
        self.connect_btn.setFixedWidth(80)
        self.connect_btn.clicked.connect(self.toggle_connection)
        config_layout.addWidget(self.connect_btn)

        # 错误信息显示标签
        self.error_label = QLabel()
        self.error_label.setStyleSheet("""
                    color: red; 
                    font-size: 13px;
                    font-weight: bold;
                    padding: 2px;
                """)
        self.error_label.setWordWrap(True)
        self.error_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        config_layout.addWidget(self.error_label)

        config_layout.addStretch()
        layout.addLayout(config_layout)

        # 接收数据显示区域
        self.receive_text = QTextEdit()
        self.receive_text.setMinimumHeight(200)
        self.receive_text.setReadOnly(True)
        self.receive_text.setLineWrapMode(QTextEdit.NoWrap)
        layout.addWidget(self.receive_text)

        # 底部按钮区域
        btn_layout = QHBoxLayout()

        self.clear_btn = QPushButton("清空")
        self.clear_btn.setFixedWidth(60)
        self.clear_btn.clicked.connect(self.clear_receive)
        btn_layout.addWidget(self.clear_btn)

        btn_layout.addStretch()

        self.save_btn = QPushButton("保存")
        self.save_btn.setFixedWidth(60)
        self.save_btn.clicked.connect(self.save_data)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def refresh_ports(self, ports: list):
        """刷新端口列表"""
        current = self.port_combo.currentText()
        self.port_combo.clear()
        self.port_combo.addItems(ports)
        if current in ports:
            self.port_combo.setCurrentText(current)
        elif ports:
            self.port_combo.setCurrentIndex(0)

    def show_error(self, message: str):
        """显示错误信息"""
        self.error_label.setText(message)
        self.error_label.setToolTip(message)  # 添加悬停提示

    def clear_error(self):
        """清除错误信息"""
        self.error_label.clear()
        self.error_label.setToolTip("")

    def toggle_connection(self):
        """切换连接状态"""
        if self.serial_receiver and self.serial_receiver.is_connected:
            self.disconnect_serial()
        else:
            self.connect_serial()

    def connect_serial(self):
        """连接串口"""
        port = self.port_combo.currentText()
        if not port:
            self.show_error("请选择串口号")
            return

        self.clear_error()  # 清除之前的错误信息

        try:
            config = SerialConfig(
                port=port,
                baudrate=int(self.baudrate_combo.currentText()))

            # 如果已有接收器，先断开
            if self.serial_receiver:
                self.serial_receiver.disconnect()

            # 创建新的接收器
            self.serial_receiver = SerialReceiver(config, self.port_index)
            self.serial_receiver.data_received.connect(self.on_data_received)
            self.serial_receiver.error_occurred.connect(self.on_serial_error)
            self.serial_receiver.start()

            self.connect_btn.setText("断开")
            self.port_combo.setEnabled(False)
            self.baudrate_combo.setEnabled(False)

        except serial.SerialException as e:
            error_msg = f"串口错误: {str(e)}"
            if "PermissionError" in str(e):
                error_msg = "串口已被占用"
            elif "FileNotFoundError" in str(e):
                error_msg = "串口不存在"
            self.show_error(error_msg)
        except ValueError as e:
            self.show_error(f"无效参数: {str(e)}")
        except Exception as e:
            self.show_error(f"未知错误: {str(e)}")

    def on_serial_error(self, error_msg: str):
        """处理串口错误信号"""
        self.show_error(error_msg)
        self.disconnect_serial()

    def disconnect_serial(self):
        """断开串口连接"""
        if self.serial_receiver:
            self.serial_receiver.disconnect()
            self.serial_receiver = None

        self.connect_btn.setText("连接")
        self.port_combo.setEnabled(True)
        self.baudrate_combo.setEnabled(True)

    def on_data_received(self, data: str):
        """数据接收回调"""
        if not self.is_receiving:
            return

        cursor = self.receive_text.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertText(data)
        self.receive_text.setTextCursor(cursor)
        self.receive_text.ensureCursorVisible()

    def clear_receive(self):
        """清空接收区"""
        self.receive_text.clear()

    def save_data(self):
        """保存数据到文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"保存串口 {self.port_index + 1} 数据",
            "",
            "Text Files (*.txt);;All Files (*)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.receive_text.toPlainText())
                QMessageBox.information(self, "成功", f"串口 {self.port_index + 1} 数据保存成功")
            except Exception as e:
                self.show_error(f"保存失败: {str(e)}")


class SerialReceiverApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("多串口数据接收器")
        self.resize(1920, 1080)

        # 接收控制变量
        self.is_receiving = True  # 默认接收数据
        self.max_ports = 8  # 默认8个串口
        self.port_widgets = []  # 存储串口控件

        # 创建界面
        self.init_ui()

    def init_ui(self):
        # 主窗口布局
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)

        # 控制面板
        control_group = QGroupBox("控制面板")
        control_layout = QHBoxLayout(control_group)

        # 串口数量选择
        control_layout.addWidget(QLabel("串口数量:"))

        self.port_count_combo = QComboBox()
        self.port_count_combo.addItems([str(i) for i in range(8, 17)])
        self.port_count_combo.setCurrentText('8')
        self.port_count_combo.currentTextChanged.connect(self.update_port_displays)
        control_layout.addWidget(self.port_count_combo)

        # 网格布局参数调整
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(12)  # 增大间距
        self.grid_layout.setContentsMargins(10, 10, 10, 10)  # 设置边距

        # 接收控制按钮
        self.receive_btn = QPushButton("停止接收")
        self.receive_btn.clicked.connect(self.toggle_receive)
        control_layout.addWidget(self.receive_btn)

        # 清空所有按钮
        self.clear_all_btn = QPushButton("清空所有")
        self.clear_all_btn.clicked.connect(self.clear_all)
        control_layout.addWidget(self.clear_all_btn)

        # 刷新端口按钮
        self.refresh_btn = QPushButton("刷新端口")
        self.refresh_btn.clicked.connect(self.refresh_all_ports)
        control_layout.addWidget(self.refresh_btn)

        control_layout.addStretch()
        main_layout.addWidget(control_group)

        # 串口显示区域容器
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        self.port_container = QWidget()
        self.port_container_layout = QVBoxLayout(self.port_container)

        # 创建网格布局用于放置串口控件
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(10)
        self.port_container_layout.addLayout(self.grid_layout)
        self.port_container_layout.addStretch()

        scroll_area.setWidget(self.port_container)
        main_layout.addWidget(scroll_area)

        self.setCentralWidget(main_widget)

        # 初始化串口显示区域
        self.create_port_widgets(8)

    def create_port_widgets(self, count: int):
        """创建指定数量的串口控件"""
        # 先清除现有控件
        for widget in self.port_widgets:
            widget.disconnect_serial()
            widget.setParent(None)

        self.port_widgets.clear()

        # 创建新的控件
        for i in range(count):
            port_widget = SerialPortWidget(i)
            self.port_widgets.append(port_widget)

            # 添加到网格布局
            row = i // 4
            col = i % 4
            self.grid_layout.addWidget(port_widget, row, col)

        # 刷新端口列表
        self.refresh_all_ports()

    def update_port_displays(self, count_str: str):
        """更新串口显示区域"""
        try:
            count = int(count_str)
            self.max_ports = count
            self.create_port_widgets(count)
        except ValueError:
            pass

    def toggle_receive(self):
        """切换接收状态"""
        self.is_receiving = not self.is_receiving
        for widget in self.port_widgets:
            widget.is_receiving = self.is_receiving

        if self.is_receiving:
            self.receive_btn.setText("停止接收")
        else:
            self.receive_btn.setText("开始接收")

    def clear_all(self):
        """清空所有接收区"""
        for widget in self.port_widgets:
            widget.clear_receive()

    def refresh_all_ports(self):
        """刷新所有串口下拉列表"""
        ports = SerialReceiver.get_available_ports()
        for widget in self.port_widgets:
            widget.refresh_ports(ports)
            widget.clear_error()  # 刷新时清除错误信息

    def closeEvent(self, event):
        """窗口关闭事件处理"""
        for widget in self.port_widgets:
            widget.disconnect_serial()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SerialReceiverApp()
    window.show()
    sys.exit(app.exec_())