import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from serial_receiver import SerialReceiver, SerialConfig


class SerialReceiverApp:
    def __init__(self, root):
        self.root = root
        self.root.title("多串口数据接收器")
        self.root.geometry("1000x700")

        # 接收控制变量
        self.is_receiving = False
        self.max_ports = 8  # 默认8个串口
        self.active_receivers = []  # 存储活动的接收器

        # 创建界面
        self.create_widgets()
        self.active_receivers = [None] * 16  # 初始化为16个None，足够最大需求

    def create_widgets(self):
        """创建程序界面组件"""
        # 主布局
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 控制面板
        control_frame = tk.LabelFrame(main_frame, text="控制面板")
        control_frame.pack(fill=tk.X, pady=(0, 10))

        # 串口数量选择
        tk.Label(control_frame, text="串口数量:").grid(row=0, column=0, padx=5, pady=5)
        self.port_count = ttk.Combobox(control_frame, values=list(range(8, 17)), width=5)
        self.port_count.grid(row=0, column=1, padx=5, pady=5)
        self.port_count.set(8)
        self.port_count.bind("<<ComboboxSelected>>", self.update_port_displays)

        # 接收控制按钮
        self.receive_btn = tk.Button(control_frame, text="开始接收", command=self.toggle_receive)
        self.receive_btn.grid(row=0, column=2, padx=5, pady=5)

        # 清空所有按钮
        self.clear_btn = tk.Button(control_frame, text="清空所有", command=self.clear_all)
        self.clear_btn.grid(row=0, column=3, padx=5, pady=5)

        # 刷新端口按钮
        self.refresh_btn = tk.Button(control_frame, text="刷新端口", command=self.refresh_all_ports)
        self.refresh_btn.grid(row=0, column=5, padx=5, pady=5)

        # 串口显示区域容器
        self.display_container = tk.Frame(main_frame)
        self.display_container.pack(fill=tk.BOTH, expand=True)

        # 初始化串口显示区域
        self.port_frames = []
        self.port_comboboxes = []
        self.baudrate_comboboxes = []
        self.receive_texts = []
        self.connect_btns = []
        self.save_btns = []

        # 创建初始8个串口显示区域
        for i in range(8):
            # 每个串口的框架
            port_frame = tk.LabelFrame(self.display_container, text=f"串口 {i + 1}")
            port_frame.grid(row=i // 4, column=i % 4, padx=5, pady=5, sticky="nsew")
            self.display_container.grid_columnconfigure(i % 4, weight=1)
            self.port_frames.append(port_frame)

            # 配置区域
            config_frame = tk.Frame(port_frame)
            config_frame.pack(fill=tk.X, padx=5, pady=2)

            # 串口号选择
            port_combobox = ttk.Combobox(config_frame, width=12)
            port_combobox.pack(side=tk.LEFT, padx=2)
            self.port_comboboxes.append(port_combobox)

            # 波特率选择
            baudrate_combobox = ttk.Combobox(config_frame,
                                             values=['9600', '19200', '38400', '57600', '115200'],
                                             width=8)
            baudrate_combobox.pack(side=tk.LEFT, padx=2)
            baudrate_combobox.set('9600')
            self.baudrate_comboboxes.append(baudrate_combobox)

            # 连接按钮
            connect_btn = tk.Button(config_frame, text="连接",
                                    command=lambda idx=i: self.toggle_connection(idx))
            connect_btn.pack(side=tk.LEFT, padx=2)
            self.connect_btns.append(connect_btn)

            # 接收数据显示区域
            receive_text = scrolledtext.ScrolledText(port_frame, wrap=tk.WORD,
                                                     state='disabled', height=10)
            receive_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            self.receive_texts.append(receive_text)

            # 底部按钮区域
            btn_frame = tk.Frame(port_frame)
            btn_frame.pack(fill=tk.X, padx=5, pady=2)

            # 清空按钮
            clear_btn = tk.Button(btn_frame, text="清空",
                                  command=lambda idx=i: self.clear_receive(idx))
            clear_btn.pack(side=tk.LEFT, padx=2)

            # 保存按钮
            save_btn = tk.Button(btn_frame, text="保存",
                                 command=lambda idx=i: self.save_data(idx))
            save_btn.pack(side=tk.RIGHT, padx=2)
            self.save_btns.append(save_btn)

        # 初始化时刷新端口列表
        self.refresh_all_ports()

    def toggle_receive(self):
        """切换接收状态"""
        self.is_receiving = not self.is_receiving
        if self.is_receiving:
            self.receive_btn.config(text="停止接收")
            print("开始接收数据...")
        else:
            self.receive_btn.config(text="开始接收")
            print("停止接收数据...")

    def clear_receive(self, index):
        """清空单个串口接收区"""
        self.receive_texts[index].config(state='normal')
        self.receive_texts[index].delete(1.0, tk.END)
        self.receive_texts[index].config(state='disabled')

    def update_port_displays(self, event=None):
        """更新串口显示区域"""
        # 清除现有显示
        for widget in self.display_container.winfo_children():
            widget.destroy()

        self.port_frames = []
        self.port_comboboxes = []
        self.baudrate_comboboxes = []
        self.receive_texts = []
        self.connect_btns = []
        self.save_btns = []  # 新增保存按钮列表
        self.active_receivers = [None] * self.max_ports

        # 获取新的串口数量
        try:
            self.max_ports = int(self.port_count.get())
        except:
            self.max_ports = 8
            self.port_count.set(8)

        # 创建新的显示区域
        for i in range(self.max_ports):
            # 每个串口的框架
            port_frame = tk.LabelFrame(self.display_container, text=f"串口 {i + 1}")
            port_frame.grid(row=i // 4, column=i % 4, padx=5, pady=5, sticky="nsew")
            self.display_container.grid_columnconfigure(i % 4, weight=1)
            self.display_container.grid_rowconfigure(i // 4, weight=1)
            self.port_frames.append(port_frame)

            # 串口配置
            config_frame = tk.Frame(port_frame)
            config_frame.pack(fill=tk.X, padx=5, pady=2)

            # 串口号选择
            port_combobox = ttk.Combobox(config_frame, width=12)
            port_combobox.pack(side=tk.LEFT, padx=2)
            self.port_comboboxes.append(port_combobox)

            # 波特率选择
            baudrate_combobox = ttk.Combobox(config_frame,
                                             values=['9600', '19200', '38400', '57600', '115200'],
                                             width=8)
            baudrate_combobox.pack(side=tk.LEFT, padx=2)
            baudrate_combobox.set('9600')
            self.baudrate_comboboxes.append(baudrate_combobox)

            # 连接按钮
            connect_btn = tk.Button(config_frame, text="连接",
                                    command=lambda idx=i: self.toggle_connection(idx))
            connect_btn.pack(side=tk.LEFT, padx=2)
            self.connect_btns.append(connect_btn)

            # 接收数据显示区域
            receive_text = scrolledtext.ScrolledText(port_frame, wrap=tk.WORD,
                                                     state='disabled', height=10)
            receive_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            self.receive_texts.append(receive_text)

            # 底部按钮区域 - 新增部分
            btn_frame = tk.Frame(port_frame)
            btn_frame.pack(fill=tk.X, padx=5, pady=2)

            # 清空按钮
            clear_btn = tk.Button(btn_frame, text="清空",
                                  command=lambda idx=i: self.clear_receive(idx))
            clear_btn.pack(side=tk.LEFT, padx=2)

            # 保存按钮
            save_btn = tk.Button(btn_frame, text="保存",
                                 command=lambda idx=i: self.save_data(idx))
            save_btn.pack(side=tk.RIGHT, padx=2)
            self.save_btns.append(save_btn)  # 将保存按钮添加到列表中

        # 刷新所有端口列表
        self.refresh_all_ports()

    def refresh_all_ports(self):
        """刷新所有串口下拉列表"""
        ports = SerialReceiver.get_available_ports(None)  # 调用静态方法
        for combobox in self.port_comboboxes:
            combobox['values'] = ports
            if ports:
                combobox.set(ports[0])

    def toggle_connection(self, index):
        """切换单个串口的连接状态"""
        if hasattr(self.active_receivers[index], 'is_connected') and self.active_receivers[index].is_connected:
            self.disconnect_serial(index)
        else:
            self.connect_serial(index)

    def toggle_connection(self, index):
        """切换单个串口的连接状态"""
        # 检查列表长度是否足够
        while len(self.active_receivers) <= index:
            self.active_receivers.append(None)

        # 检查是否有接收器实例且已连接
        if (self.active_receivers[index] is not None and
                hasattr(self.active_receivers[index], 'is_connected') and
                self.active_receivers[index].is_connected):
            self.disconnect_serial(index)
        else:
            self.connect_serial(index)

    def connect_serial(self, index):
        """连接单个串口"""
        port = self.port_comboboxes[index].get()
        if not port:
            messagebox.showerror("错误", f"串口 {index + 1} 请选择串口号")
            return

        try:
            config = SerialConfig(
                port=port,
                baudrate=int(self.baudrate_comboboxes[index].get())
            )

            # 确保列表长度足够
            while len(self.active_receivers) <= index:
                self.active_receivers.append(None)

            # 如果已有接收器，先断开
            if self.active_receivers[index] is not None:
                self.active_receivers[index].disconnect()

            # 创建新的接收器
            receiver = SerialReceiver(lambda data, idx=index: self.on_data_received(data, idx))
            if receiver.connect(config):
                self.active_receivers[index] = receiver
                self.connect_btns[index].config(text="断开")
                self.port_comboboxes[index].config(state='disabled')
                self.baudrate_comboboxes[index].config(state='disabled')
        except Exception as e:
            messagebox.showerror("错误", f"串口 {index + 1} 无法打开:\n{str(e)}")

    def disconnect_serial(self, index):
        """断开单个串口连接"""
        # 检查列表长度是否足够
        if index >= len(self.active_receivers) or self.active_receivers[index] is None:
            return

        self.active_receivers[index].disconnect()
        self.connect_btns[index].config(text="连接")
        self.port_comboboxes[index].config(state='normal')
        self.baudrate_comboboxes[index].config(state='normal')
        self.active_receivers[index] = None

    def on_data_received(self, data: str, index: int):
        """数据接收回调函数"""
        try:
            if not self.is_receiving:
                return

            self.receive_texts[index].config(state='normal')
            self.receive_texts[index].insert(tk.END, data)
            self.receive_texts[index].see(tk.END)
            self.receive_texts[index].config(state='disabled')
        except Exception as e:
            print(f"Error updating display for port {index}: {e}")

    def clear_all(self):
        """清空所有接收区"""
        for text in self.receive_texts:
            text.config(state='normal')
            text.delete(1.0, tk.END)
            text.config(state='disabled')

    def save_data(self, index):
        """保存单个串口数据"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            title=f"保存串口 {index + 1} 数据"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    content = self.receive_texts[index].get(1.0, tk.END)
                    f.write(content)
                messagebox.showinfo("成功", f"串口 {index + 1} 数据保存成功")
            except Exception as e:
                messagebox.showerror("错误", f"串口 {index + 1} 保存失败:\n{str(e)}")

    def on_closing(self):
        """窗口关闭事件处理"""
        for i in range(len(self.active_receivers)):
            self.disconnect_serial(i)
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = SerialReceiverApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()