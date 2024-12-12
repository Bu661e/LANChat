from PySide6.QtWidgets import (QWidget, QTextEdit, QLineEdit, QPushButton, 
                             QVBoxLayout, QHBoxLayout, QListWidget, QSplitter,
                             QLabel, QFrame, QStackedWidget, QListWidgetItem,
                             QMessageBox)
from PySide6.QtCore import Qt, QSize
from datetime import datetime

class ChatPanel(QWidget):
    """聊天面板组件，用于群聊或私聊"""
    def __init__(self, title="群聊"):
        super().__init__()
        self.initUI(title)
        
    def initUI(self, title):
        layout = QVBoxLayout()
        
        # 添加标题标签
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("QLabel { font-size: 14px; font-weight: bold; padding: 5px; }")
        layout.addWidget(self.title_label)
        
        # 聊天记录显示区域
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)
        
        # 创建输入区域
        input_widget = QWidget()
        input_layout = QVBoxLayout()
        
        # 工具栏
        toolbar = QHBoxLayout()
        input_layout.addLayout(toolbar)
        
        # 消息输入框
        self.message_input = QTextEdit()
        self.message_input.setMaximumHeight(100)
        self.message_input.setPlaceholderText("请输入消息...")
        input_layout.addWidget(self.message_input)
        
        # 发送按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.send_button = QPushButton("发送")
        self.send_button.setFixedWidth(60)
        button_layout.addWidget(self.send_button)
        input_layout.addLayout(button_layout)
        
        input_widget.setLayout(input_layout)
        input_widget.setMaximumHeight(150)
        layout.addWidget(input_widget)
        
        self.setLayout(layout)

class ChatWindow(QWidget):
    def __init__(self, client=None):
        super().__init__()
        self.client = client
        self.chat_panels = {}  # 使用 "ip:port" 作为key
        self.current_chat = None
        self.initUI()
        
        # 连接客户端信号
        if self.client:
            self.client.new_user_login.connect(self.handle_new_user_login)
            self.client.old_friend_list.connect(self.handle_old_friend_list)
            self.client.user_logout.connect(self.handle_user_logout)
            self.client.new_message.connect(self.handle_new_message)
            self.client.new_private_message.connect(self.handle_private_message)  # 添加私聊信号连接
        
    def initUI(self):
        # 设置窗口标题和大小
        self.setWindowTitle('局域网聊天室')
        self.resize(800, 600)
        
        # 创建主布局
        main_layout = QHBoxLayout()
        
        # 创建左侧在线用户列表面板
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        
        # 创建左侧在线用户列表
        self.user_list = QListWidget()
        self.user_list.setMinimumWidth(150)
        
        # 添加固定的广场选项
        square_item = QListWidgetItem("广场")
        square_item.setData(Qt.UserRole, "group")  # 存储特殊标识
        square_item.setFlags(square_item.flags() | Qt.ItemIsEnabled)  # 确保可点击
        self.user_list.addItem(square_item)
        
        # 添加分隔线
        separator_item = QListWidgetItem()
        separator_item.setFlags(Qt.NoItemFlags)  # 使分隔线不可选
        separator_item.setBackground(Qt.gray)
        separator_item.setSizeHint(QSize(0, 1))  # 设置分隔线高度
        self.user_list.addItem(separator_item)
        
        left_layout.addWidget(QLabel("在线用户"))
        left_layout.addWidget(self.user_list)
        
        # 添加退出按钮
        self.logout_btn = QPushButton("退出登录")
        self.logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #d9534f;
                color: white;
                padding: 5px;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #c9302c;
            }
        """)
        left_layout.addWidget(self.logout_btn)
        
        left_widget.setLayout(left_layout)
        
        # 创建右侧聊天区域
        self.chat_stack = QStackedWidget()
        
        # 创建群聊面板
        self.group_chat = ChatPanel("广场")  # 修改标题为"广场"
        self.chat_stack.addWidget(self.group_chat)
        self.chat_panels["group"] = self.group_chat
        self.current_chat = "group"
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(self.chat_stack)
        
        # 设置分割器的初始大小比例
        splitter.setSizes([200, 600])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        splitter.setHandleWidth(5)
        
        # 添加分割器到主布局
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
        
        # 接收槽
        self.user_list.itemClicked.connect(self.on_user_clicked)
        self.group_chat.send_button.clicked.connect(self.send_message)
        self.logout_btn.clicked.connect(self.logout)
        
    def on_user_clicked(self, item):
        """处理用户列表点击事件"""
        # 检查是否是广场
        if item.data(Qt.UserRole) == "group":
            self.chat_stack.setCurrentWidget(self.chat_panels["group"])
            self.current_chat = "group"
            return
            
        user_info = item.text()  # 格式: "username (ip:port)"
        username = user_info.split(" (")[0]
        address = user_info.split(" (")[1].rstrip(")")  # 获取 "ip:port"
        
        # 如果是新的私聊，创建新的聊天面板
        if address not in self.chat_panels:
            private_chat = ChatPanel(f"与 {username} ({address}) 私聊中")
            private_chat.send_button.clicked.connect(self.send_message)
            self.chat_stack.addWidget(private_chat)
            self.chat_panels[address] = private_chat
            
        # 切换到对应的聊天面板
        self.chat_stack.setCurrentWidget(self.chat_panels[address])
        self.current_chat = address
        
    def add_user(self, username, ip):
        """添加在线用户到列表"""
        # 在分隔线添加用户
        self.user_list.addItem(f"{username} ({ip})")
        
    def remove_user(self, username, address):
        """从列表中移除用户"""
        items = self.user_list.findItems(f"{username} ({address})", Qt.MatchExactly)
        for item in items:
            self.user_list.takeItem(self.user_list.row(item))
        
        # 如果存在该用户的私聊面板，也需要移除
        if address in self.chat_panels:
            panel = self.chat_panels[address]
            self.chat_stack.removeWidget(panel)
            del self.chat_panels[address]
            # 如果当前正在查看该用户的私聊，切换回群聊
            if self.current_chat == address:
                self.chat_stack.setCurrentWidget(self.chat_panels["group"])
                self.current_chat = "group"

    def add_message(self, username, message, to_address=None):
        """添加消息到聊天记录
        username: 发送消息的用户
        message: 消息内容
        to_address: 私聊目标用户地址，None表示群聊消息
        """
        if to_address:
            # 私聊消息
            if to_address in self.chat_panels:
                self.chat_panels[to_address].chat_display.append(f"{username}: {message}")
        else:
            # 群聊消息
            self.chat_panels["group"].chat_display.append(f"{username}: {message}")
        
    def send_message(self):
        """发送消息"""
        current_panel = self.chat_panels[self.current_chat]
        message = current_panel.message_input.toPlainText().strip()
        if message:
            time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if self.current_chat == "group":  # 广场消息
                self.client.send_message({
                    "type": "square_message",
                    "content": message,
                    "timestamp": time
                })
                current_panel.chat_display.append(f"[{time}]【我】: {message}")
            else:  # 私聊消息
                target_ip, target_port = self.current_chat.split(":")
                self.client.send_message({
                    "type": "private_message",
                    "target_ip": target_ip,
                    "target_port": target_port,
                    "content": message,
                    "timestamp": time
                })
                current_panel.chat_display.append(f"{time}【我】: {message}")
            current_panel.message_input.clear()
            
    def clear_chat(self):
        """清空当前聊天记录"""
        current_panel = self.chat_panels[self.current_chat]
        current_panel.chat_display.clear()
        
    def logout(self):
        """处理退出登录"""
        reply = QMessageBox.question(
            self,
            "确认退出",
            "确定要退出登录吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 发送登出消息给服务器
            if self.client:
                try:
                    self.client.send_message({
                        "type": "logout",

                    })
                    # self.client.close()
                except:
                    pass  # 忽略发送登出消息时的错误
                    
            # 关闭程序
            self.close()
            # 确保程序全退出
            import sys
            sys.exit(0)
        
    def handle_new_user_login(self, username, ip, port):
        """处理新用户登录"""
        # 添加用户到列表
        self.add_user(username, f"{ip}:{port}")
        
        # 在广场聊天中显示系统消息
        self.chat_panels["group"].chat_display.append(
            f"【系统消息】: {username} ({ip}:{port}) 加入了聊天室"
        )
        
    def handle_old_friend_list(self, users):
        """处理已有用户列表"""
        # 清空现有用户列表（保留广场和分隔线）
        while self.user_list.count() > 2:
            self.user_list.takeItem(2)

        print(f"处理已有用户列表: {users}")

        # 添加所有用户到列表
        for user in users:
            username = user.get('username')
            address = user.get('address')
            ip, port = address
            self.add_user(username, f"{ip}:{port}")
            print(f"添加用户到列表: {username} ({ip}:{port})")  # 添加调试信息
                    
    def handle_user_logout(self, username, ip, port):
        """处理用户登出"""
        # 从用户列表中移除用户
        self.remove_user(username, f"{ip}:{port}")
        
        # 在广场聊天中显示系统消息
        self.chat_panels["group"].chat_display.append(
            f"【系统消息】: {username} ({ip}:{port}) 离开了聊天室"
        )
                    
    def handle_new_message(self, username, ip, port, content, timestamp):
        """处理群聊消息"""
        self.chat_panels["group"].chat_display.append(
            f"[{timestamp}] {username} ({ip}): {content}"
        )
                    
    def handle_private_message(self, username, ip, port, content, timestamp):
        """处理私聊消息"""
        address = f"{ip}:{port}"
        
        # 如果没有对应的聊天面板，创建一个
        if address not in self.chat_panels.keys():
            private_chat = ChatPanel(f"与 {username} ({address}) 私聊中")
            private_chat.send_button.clicked.connect(self.send_message)
            self.chat_stack.addWidget(private_chat)
            self.chat_panels[address] = private_chat
        
        # 添加消息到对应的聊天面板
        self.chat_panels[address].chat_display.append(
            f"[{timestamp}] {username}: {content}"
        )
                    
