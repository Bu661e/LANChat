from PySide6.QtWidgets import (QWidget, QLineEdit, QPushButton, 
                             QVBoxLayout, QHBoxLayout, QLabel, QFormLayout,
                             QMessageBox)
from PySide6.QtCore import Qt
import json
import os
from client import Client
from chat_ui import ChatWindow

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.config_file = os.path.join(os.path.dirname(__file__), 'conf.json')
        self.client = Client()
        self.chat_window = None
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
    
    def initUI(self):
        self.setWindowTitle('登录')
        self.setFixedSize(400, 600)
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f6fa;
                color: #2c3e50;
                font-size: 14px;
            }
            QLabel {
                font-size: 14px;
                color: #34495e;
                padding: 5px;
                margin-top: 5px;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                background-color: white;
                margin-bottom: 10px;
                height: 20px;
            }
            QLineEdit:focus {
                border: 1px solid #3498db;
            }
            QPushButton {
                padding: 8px 20px;
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                height: 36px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #2472a4;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # 添加标题
        title = QLabel("局域网聊天室")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
                margin-bottom: 10px;
            }
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 添加说明文字
        desc = QLabel("请输入连接信息")
        desc.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #7f8c8d;
                padding: 5px;
                margin-bottom: 15px;
            }
        """)
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)
        
        # 创建表单布局
        form_layout = QFormLayout()
        form_layout.setSpacing(5)
        
        # 创建输入框
        self.server_ip = QLineEdit()
        self.server_ip.setPlaceholderText("请输入服务器IP地址")
        form_layout.addRow('服务器IP:', self.server_ip)
        
        self.server_port = QLineEdit()
        self.server_port.setPlaceholderText("请输入服务器端口")
        form_layout.addRow('服务器端口:', self.server_port)
        
        self.local_ip = QLineEdit()
        self.local_ip.setPlaceholderText("请输入本地IP地址")
        form_layout.addRow('本地IP:', self.local_ip)
        
        self.local_port = QLineEdit()
        self.local_port.setPlaceholderText("请输入本地端口")
        form_layout.addRow('本地端口:', self.local_port)
        
        self.username = QLineEdit()
        self.username.setPlaceholderText("请输入用户名")
        form_layout.addRow('用户名:', self.username)
        
        layout.addLayout(form_layout)
        
        # 添加一些空间
        layout.addSpacing(20)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        # 创建按钮
        self.confirm_btn = QPushButton("连接")
        self.reset_btn = QPushButton("重置")
        
        # 设置按钮样式
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:pressed {
                background-color: #219a52;
            }
        """)
        
        button_layout.addWidget(self.confirm_btn)
        button_layout.addWidget(self.reset_btn)
        layout.addLayout(button_layout)
        
        # 添加版权信息
        copyright = QLabel("© 2024 局域网聊天室")
        copyright.setStyleSheet("""
            QLabel {
                color: #95a5a6;
                font-size: 12px;
                padding: 5px;
                margin-top: 10px;
            }
        """)
        copyright.setAlignment(Qt.AlignCenter)
        layout.addWidget(copyright)
        
        self.setLayout(layout)

    def try_connect(self):
        """尝试连接服务器"""
        server_ip = self.server_ip.text().strip()
        server_port = self.server_port.text().strip()
        local_ip = self.local_ip.text().strip()
        local_port = self.local_port.text().strip()
        username = self.username.text().strip()
        
        if not all([server_ip, server_port, local_ip, local_port, username]):
            QMessageBox.warning(self, "输入错误", "请填写所有字段")
            return
        
        try:
            self.save_config()
            self.confirm_btn.setEnabled(False)
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