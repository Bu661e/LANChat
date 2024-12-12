from PySide6.QtWidgets import (QWidget, QLineEdit, QPushButton, 
                             QVBoxLayout, QHBoxLayout, QLabel, QFormLayout,
                             QMessageBox)
from PySide6.QtCore import Qt
import json
import os
from client import Client
from chat_ui import ChatWindow  # 导入聊天界面

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.config_file = os.path.join(os.path.dirname(__file__), 'conf.json')
        self.client = Client()  # 创建客户端实例
        self.chat_window = None  # 初始化聊天窗口为None
        self.initUI()
        self.load_config()
        self.setup_connections()
        
    def setup_connections(self):
        """设置信号连接"""
        self.confirm_btn.clicked.connect(self.try_connect)
        self.reset_btn.clicked.connect(self.load_config)
        
        # 连接客户端信号
        self.client.connected.connect(self.on_connected)
        self.client.connection_failed.connect(self.on_connection_failed)
    
    def try_connect(self):
        """尝试连接服务器"""
        # 获���输入信息
        server_ip = self.server_ip.text().strip()
        server_port = self.server_port.text().strip()
        local_ip = self.local_ip.text().strip()
        local_port = self.local_port.text().strip()
        username = self.username.text().strip()
        
        # 验证输入
        if not all([server_ip, server_port, local_ip, local_port, username]):
            QMessageBox.warning(self, "输入错误", "请填写所有字段")
            return
        
        try:
            # 保存配置
            self.save_config()
            
            # 尝试连接
            self.confirm_btn.setEnabled(False)  # 禁用按钮防止重复点击
            self.client.connect_to_server(
                server_ip, server_port,
                local_ip, local_port,
                username
            )
            
        except Exception as e:
            QMessageBox.critical(self, "连接错误", f"连接失败: {str(e)}")
            self.confirm_btn.setEnabled(True)
    
    def on_connected(self):
        """连接成功的处理"""
        # 创建并显示聊天界面，传入客户端实例
        self.chat_window = ChatWindow(self.client)
        self.chat_window.show()
        
        # 关闭登录界面
        self.close()
        
    def on_connection_failed(self, error_message):
        """连接失败的处理"""
        QMessageBox.critical(self, "连接失败", f"无法连接到服务器: {error_message}")
        self.confirm_btn.setEnabled(True)

    def initUI(self):
        # 设置窗口标题和大小
        self.setWindowTitle('聊天室登录')
        self.resize(400, 250)
        
        # 创建表单布局
        form_layout = QFormLayout()
        
        # 创建输入框
        self.server_ip = QLineEdit()
        self.server_port = QLineEdit()
        self.local_ip = QLineEdit()
        self.local_port = QLineEdit()
        self.username = QLineEdit()
        
        # 添加输入框到表单布局
        form_layout.addRow('服务器IP:', self.server_ip)
        form_layout.addRow('服务器端口:', self.server_port)
        form_layout.addRow('本机IP:', self.local_ip)
        form_layout.addRow('本机端口:', self.local_port)
        form_layout.addRow('用户名:', self.username)
        
        # 创建按钮布局
        btn_layout = QHBoxLayout()

        # 创建按钮
        self.confirm_btn = QPushButton('确认')
        self.reset_btn = QPushButton('重置')
        
        # 添加按钮到水平布局
        btn_layout.addWidget(self.confirm_btn)
        btn_layout.addWidget(self.reset_btn)
        
        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.addLayout(form_layout)
        main_layout.addLayout(btn_layout)
        
        # 设置主布局
        self.setLayout(main_layout)
        
        # 连接信号和槽
        self.reset_btn.clicked.connect(self.load_config)
        self.confirm_btn.clicked.connect(self.save_config)
    
    def get_default_config(self):
        """返回默认配置"""
        return {
            'server_ip': '127.0.0.1',
            'server_port': '8000',
            'local_ip': '127.0.0.1',
            'local_port': '8001',
            'username': 'username'
        }
    
    def load_config(self):
        """从配置文件加载数据"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                config = self.get_default_config()
                # 如果配置文件不存在，创建默认配置文件
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=4)
                
            # 更新界面数据
            self.server_ip.setText(config.get('server_ip'))
            self.server_port.setText(config.get('server_port'))
            self.local_ip.setText(config.get('local_ip'))
            self.local_port.setText(config.get('local_port'))
            self.username.setText(config.get('username'))
            
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            # 加载失败时使用默认值
            config = self.get_default_config()
            self.server_ip.setText(config['server_ip'])
            self.server_port.setText(config['server_port'])
            self.local_ip.setText(config['local_ip'])
            self.local_port.setText(config['local_port'])
            self.username.setText(config['username'])
    
    def save_config(self):
        """保存当前配置到文件"""
        config = {
            'server_ip': self.server_ip.text(),
            'server_port': self.server_port.text(),
            'local_ip': self.local_ip.text(),
            'local_port': self.local_port.text(),
            'username': self.username.text()
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存配置文件败: {e}") 