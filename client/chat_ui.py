from PySide6.QtWidgets import (QWidget, QTextEdit, QLineEdit, QPushButton, 
                             QVBoxLayout, QHBoxLayout, QListWidget, QSplitter,
                             QLabel, QFrame, QStackedWidget, QListWidgetItem,
                             QMessageBox, QFileDialog, QMenu)
from PySide6.QtCore import Qt, QSize, QPoint
from PySide6.QtGui import QAction, QCursor
from datetime import datetime
import base64
import os

class ChatPanel(QWidget):
    """聊天面板组件，用于群聊或私聊"""
    def __init__(self, title="广场"):
        super().__init__()
        self.initUI(title)
        
    def initUI(self, title):
        layout = QVBoxLayout()
        layout.setSpacing(10)  # 设置布局间距
        
        # 美化标题标签
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
                background-color: #ecf0f1;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.title_label)
        
        # 美化聊天记录显示区域
        self.chat_display = ImageTextEdit()  # 使用自定义的ImageTextEdit
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                padding: 10px;
                background-color: white;
                font-size: 14px;
                line-height: 1.6;
            }
            QTextEdit p {
                margin: 8px 0;
            }
        """)
        layout.addWidget(self.chat_display)
        
        # 创建输入区域
        input_widget = QWidget()
        input_layout = QVBoxLayout()
        input_layout.setSpacing(8)
        
        # 消息输入框
        self.message_input = QTextEdit()
        self.message_input.setMaximumHeight(100)
        self.message_input.setPlaceholderText("请输入消息...")
        self.message_input.setStyleSheet("""
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
                background-color: white;
            }
        """)
        input_layout.addWidget(self.message_input)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 添加发送图片按���
        self.image_button = QPushButton("发送图片")
        self.image_button.setFixedSize(80, 32)
        self.image_button.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:pressed {
                background-color: #219a52;
            }
        """)
        button_layout.addWidget(self.image_button)
        
        # 发送按钮
        self.send_button = QPushButton("发送")
        self.send_button.setFixedSize(80, 32)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #2472a4;
            }
        """)
        button_layout.addWidget(self.send_button)
        
        input_layout.addLayout(button_layout)
        input_widget.setLayout(input_layout)
        input_widget.setMaximumHeight(150)
        layout.addWidget(input_widget)
        
        self.setLayout(layout)

class ImageTextEdit(QTextEdit):
    def __init__(self):
        super().__init__()
        self.image_data = {}  # 存储图片数据的字典
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, position):
        cursor = self.cursorForPosition(position)
        char_format = cursor.charFormat()
        
        # 检查光标位置是否在图片上
        if char_format.isImageFormat():
            image_name = char_format.toolTip()
            if image_name in self.image_data:
                menu = QMenu(self)
                save_action = QAction("保存图片", self)
                save_action.triggered.connect(lambda: self.save_image(image_name))
                menu.addAction(save_action)
                menu.exec_(QCursor.pos())

    def save_image(self, image_name):
        if image_name not in self.image_data:
            return
            
        image_info = self.image_data[image_name]
        image_data = image_info['data']
        image_ext = image_info['ext']
        
        # 打开文件保存对话框
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(
            self,
            "保存图片",
            f"image{image_ext}",  # 默认文件名
            f"图片文件 (*{image_ext});;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                # 解码Base64数据并保存为文件
                image_bytes = base64.b64decode(image_data)
                with open(file_path, 'wb') as f:
                    f.write(image_bytes)
                QMessageBox.information(self, "成功", "图片保存成功！")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"保存图片失败：{str(e)}")

class ChatWindow(QWidget):
    def __init__(self, client=None):
        super().__init__()
        self.client = client
        self.chat_panels = {}
        self.current_chat = None
        
        # 创建聊天面板堆栈
        self.chat_stack = QStackedWidget()
        
        # 创建群聊面板
        self.group_chat = ChatPanel("广场")
        self.group_chat.send_button.clicked.connect(self.send_message)
        self.group_chat.image_button.clicked.connect(self.send_image)  # 连接图片发送按钮
        self.chat_stack.addWidget(self.group_chat)
        self.chat_panels["group"] = self.group_chat
        self.current_chat = "group"
        
        self.initUI()
        
        # 连接客户端信号
        if self.client:
            self.client.new_user_login.connect(self.handle_new_user_login)
            self.client.old_friend_list.connect(self.handle_old_friend_list)
            self.client.user_logout.connect(self.handle_user_logout)
            self.client.new_message.connect(self.handle_new_message)
            self.client.new_private_message.connect(self.handle_private_message)
            self.client.new_image_message.connect(self.handle_image_message)  # 添加图片消息处理
        
        # 连接用户列表点击事件
        self.user_list.itemClicked.connect(self.on_user_clicked)
        # 连接退出按钮事件
        self.logout_btn.clicked.connect(self.logout)
        
        # 自动选中广场选项
        self.user_list.setCurrentRow(0)

    def initUI(self):
        self.setWindowTitle('局域网聊天室')
        self.resize(1000, 700)  # 调整窗口大小
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f6fa;
                color: #2c3e50;
            }
        """)
        
        main_layout = QHBoxLayout()
        main_layout.setSpacing(15)  # 设置布局间距
        
        # 左侧面板
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setSpacing(10)
        
        # 添加当前用户信息
        user_info = QLabel(
                          f"用户名：{self.client.username}\n"
                          f"IP：  {self.client.local_ip}\n"
                          f"端口：  {self.client.local_port}")
        user_info.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #34495e;
                padding: 10px;
                background-color: #ecf0f1;
                border-radius: 5px;
                margin-bottom: 5px;
            }
        """)
        left_layout.addWidget(user_info)
        
        # 用户列表标题（包含人数）
        self.user_list_label = QLabel("在线用户 (1)")  # 初始显示1是因为包含自己
        self.user_list_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
                background-color: #ecf0f1;
                border-radius: 5px;
            }
        """)
        left_layout.addWidget(self.user_list_label)
        
        # 美化用户列表
        self.user_list = QListWidget()
        self.user_list.setMinimumWidth(200)
        self.user_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                padding: 5px;
                background-color: white;
                font-size: 14px;
                outline: none;  /* 去掉选中项的虚线边框 */
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QListWidget::item:selected:hover {
                background-color: #3498db;  /* 选中项悬停时保持选中的颜色 */
            }
            QListWidget::item:hover:!selected {
                background-color: #ecf0f1;  /* 未选中项悬停时的颜色 */
            }
        """)
        
        # 添加广场选项
        square_item = QListWidgetItem("🏠 广场")  # 添加emoji图标
        square_item.setData(Qt.UserRole, "group")
        square_item.setFlags(square_item.flags() | Qt.ItemIsEnabled)
        self.user_list.addItem(square_item)
        
        # 添加分隔线
        separator_item = QListWidgetItem()
        separator_item.setFlags(Qt.NoItemFlags)
        separator_item.setSizeHint(QSize(0, 1))
        self.user_list.addItem(separator_item)
        
        left_layout.addWidget(self.user_list)
        
        # 美化退出按钮
        self.logout_btn = QPushButton("退出登录")
        self.logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        left_layout.addWidget(self.logout_btn)
        
        left_widget.setLayout(left_layout)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(self.chat_stack)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #bdc3c7;
                width: 2px;
            }
        """)
        
        # 设置分割器的初始大小比例
        splitter.setSizes([250, 750])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
        
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
            private_chat.image_button.clicked.connect(self.send_image)  # 连接图片发送按钮
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
            # 如果前正在查看该用户的私聊，切换回群聊
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
                header = f"[{time}] 【我】"
                current_panel.chat_display.append(f"<p style='color:#2c3e50;'>{header}</p>")
                current_panel.chat_display.append(f"<p style='margin-left:20px;color:#34495e;'>{message}</p>")
            else:  # 私聊消息
                target_ip, target_port = self.current_chat.split(":")
                self.client.send_message({
                    "type": "private_message",
                    "target_ip": target_ip,
                    "target_port": target_port,
                    "content": message,
                    "timestamp": time
                })
                header = f"[{time}] 【我】"
                current_panel.chat_display.append(f"<p style='color:#2c3e50;'>{header}</p>")
                current_panel.chat_display.append(f"<p style='margin-left:20px;color:#34495e;'>{message}</p>")
            current_panel.message_input.clear()
            
    def clear_chat(self):
        """清空当前聊天记录"""
        current_panel = self.chat_panels[self.current_chat]
        current_panel.chat_display.clear()
        
    def logout(self):
        """处理退出登录"""
        # 创建确认对话框
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("确认退出")
        msg_box.setText("确定要退出登录吗？")
        msg_box.setIcon(QMessageBox.Question)
        
        # ���置按钮
        yes_btn = msg_box.addButton("确定", QMessageBox.YesRole)
        no_btn = msg_box.addButton("取消", QMessageBox.NoRole)
        
        # 设置样式
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #f5f6fa;
            }
            QLabel {
                color: #2c3e50;
                font-size: 14px;
                padding: 10px;
            }
            QPushButton {
                width: 85px;
                height: 30px;
                padding: 0 15px;
                border-radius: 4px;
                background-color: #3498db;
                color: white;
                font-size: 13px;
                font-weight: bold;
                border: none;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #2472a4;
            }
            QPushButton[text="取消"] {
                background-color: #95a5a6;
            }
            QPushButton[text="取消"]:hover {
                background-color: #7f8c8d;
            }
            QPushButton[text="取消"]:pressed {
                background-color: #707b7c;
            }
            QLabel#qt_msgbox_label { /* 消���文本 */
                min-height: 40px;
                min-width: 240px;
            }
            QLabel#qt_msgboxex_icon_label { /* 图标 */
                padding: 0;
                width: 40px;
                height: 40px;
            }
        """)
        
        # 调整对话框大小和布局
        msg_box.setMinimumWidth(300)
        
        # 获取图标标签并调整大小
        icon_label = msg_box.findChild(QLabel, "qt_msgboxex_icon_label")
        if icon_label:
            icon_label.setFixedSize(32, 32)  # 设置图标大小
        
        # 显示对话框
        reply = msg_box.exec()
        
        # 处理用户选择
        if msg_box.clickedButton() == yes_btn:
            # 发送登出消息给服务器
            if self.client:
                try:
                    self.client.send_logout_info()
                except:
                    pass  # 忽略发送登出消息时的错误
            
            # 关闭程序
            self.close()
            # 确保程序完全退出
            import sys
            sys.exit(0)
        
    def handle_new_user_login(self, username, ip, port):
        """处理新用户登录"""
        self.add_user(username, f"{ip}:{port}")
        
        # 更新用户数量
        current_count = self.user_list.count() - 1  # 减1是因为不计算分隔线
        self.user_list_label.setText(f"在线用户 ({current_count})")
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header = f"[{timestamp}] 【系统消息】"
        content = f"{username} ({ip}:{port}) 加入了聊天室"
        self.chat_panels["group"].chat_display.append(
            f"<p style='color:#7f8c8d;'>{header}</p>"
        )
        self.chat_panels["group"].chat_display.append(
            f"<p style='margin-left:20px;color:#95a5a6;'>{content}</p>"
        )
        
    def handle_old_friend_list(self, users):
        """处理已有用户列表"""
        # 清空现有用户列表（保留广场和分隔线）
        while self.user_list.count() > 2:
            self.user_list.takeItem(2)

        # 添加所有用户到列表
        for user in users:
            username = user.get('username')
            address = user.get('address')
            ip, port = address
            self.add_user(username, f"{ip}:{port}")
        
        # 更新用户数量（加2是因为包含自己和广场选项）
        self.user_list_label.setText(f"在线用户 ({len(users) + 1})")
                    
    def handle_user_logout(self, username, ip, port):
        """处理用户登出"""
        self.remove_user(username, f"{ip}:{port}")
        
        # 更新用户数量
        current_count = self.user_list.count() - 1  # 减1是因为不计算分隔线
        self.user_list_label.setText(f"在线用户 ({current_count})")
        
        # 在广场聊天中显示系统消息
        self.chat_panels["group"].chat_display.append(
            f"【系统消息】: {username} ({ip}:{port}) 离开了聊天室"
        )
                    
    def handle_new_message(self, username, ip, port, content, timestamp):
        """处理群聊消息"""
        header = f"[{timestamp}] {username} ({ip})"
        self.chat_panels["group"].chat_display.append(
            f"<p style='color:#2c3e50;'>{header}</p>"
        )
        self.chat_panels["group"].chat_display.append(
            f"<p style='margin-left:20px;color:#34495e;'>{content}</p>"
        )
                    
    def handle_private_message(self, username, ip, port, content, timestamp):
        """处理私聊消息"""
        address = f"{ip}:{port}"
        
        if address not in self.chat_panels.keys():
            private_chat = ChatPanel(f"与 {username} ({address}) 私聊中")
            private_chat.send_button.clicked.connect(self.send_message)
            self.chat_stack.addWidget(private_chat)
            self.chat_panels[address] = private_chat
        
        header = f"[{timestamp}] {username}"
        self.chat_panels[address].chat_display.append(
            f"<p style='color:#2c3e50;'>{header}</p>"
        )
        self.chat_panels[address].chat_display.append(
            f"<p style='margin-left:20px;color:#34495e;'>{content}</p>"
        )
                    
    def send_image(self):
        """处理发送图片"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, "选择图片", "", 
            "图片文件 (*.png *.jpg *.jpeg *.gif *.bmp);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                # 读取图片文件
                with open(file_path, 'rb') as f:
                    image_data = f.read()
                
                # 将图片数据转换为Base64编码
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                
                # 获取文件扩展名
                _, ext = os.path.splitext(file_path)
                
                time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                image_name = f"img_{time.replace(':', '-')}"
                
                if self.current_chat == "group":  # 广场消息
                    self.client.send_message({
                        "type": "square_image",
                        "image_data": image_base64,
                        "image_ext": ext,
                        "timestamp": time
                    })
                    
                    # 在本地显示图片
                    header = f"[{time}] 【我】"
                    current_panel = self.chat_panels[self.current_chat]
                    current_panel.chat_display.append(f"<p style='color:#2c3e50;'>{header}</p>")
                    current_panel.chat_display.append(
                        f"<p style='margin-left:20px;'><img src='data:image/{ext[1:]};base64,{image_base64}' width='400' style='max-width:90%;' title='{image_name}'/></p>"
                    )
                    # 保存图片数据
                    current_panel.chat_display.image_data[image_name] = {
                        'data': image_base64,
                        'ext': ext
                    }
                    
                else:  # 私聊消息
                    target_ip, target_port = self.current_chat.split(":")
                    self.client.send_message({
                        "type": "private_image",
                        "target_ip": target_ip,
                        "target_port": target_port,
                        "image_data": image_base64,
                        "image_ext": ext,
                        "timestamp": time
                    })
                    
                    # 在本地显示图片
                    header = f"[{time}] 【我】"
                    current_panel = self.chat_panels[self.current_chat]
                    current_panel.chat_display.append(f"<p style='color:#2c3e50;'>{header}</p>")
                    current_panel.chat_display.append(
                        f"<p style='margin-left:20px;'><img src='data:image/{ext[1:]};base64,{image_base64}' width='400' style='max-width:90%;' title='{image_name}'/></p>"
                    )
                    # 保存图片数据
                    current_panel.chat_display.image_data[image_name] = {
                        'data': image_base64,
                        'ext': ext
                    }
                    
            except Exception as e:
                QMessageBox.warning(self, "发送失败", f"图片发送失败：{str(e)}")

    def handle_image_message(self, username, ip, port, image_data, image_ext, timestamp, is_private=False):
        """处理接收到的图片消息"""
        image_name = f"img_{timestamp.replace(':', '-')}"
        
        if is_private:
            address = f"{ip}:{port}"
            if address not in self.chat_panels:
                private_chat = ChatPanel(f"与 {username} ({address}) 私聊中")
                private_chat.send_button.clicked.connect(self.send_message)
                private_chat.image_button.clicked.connect(self.send_image)
                self.chat_stack.addWidget(private_chat)
                self.chat_panels[address] = private_chat
            
            header = f"[{timestamp}] {username}"
            self.chat_panels[address].chat_display.append(
                f"<p style='color:#2c3e50;'>{header}</p>"
            )
            self.chat_panels[address].chat_display.append(
                f"<p style='margin-left:20px;'><img src='data:image/{image_ext[1:]};base64,{image_data}' width='400' style='max-width:90%;' title='{image_name}'/></p>"
            )
            # 保存图片数据
            self.chat_panels[address].chat_display.image_data[image_name] = {
                'data': image_data,
                'ext': image_ext
            }
        else:
            header = f"[{timestamp}] {username} ({ip})"
            self.chat_panels["group"].chat_display.append(
                f"<p style='color:#2c3e50;'>{header}</p>"
            )
            self.chat_panels["group"].chat_display.append(
                f"<p style='margin-left:20px;'><img src='data:image/{image_ext[1:]};base64,{image_data}' width='400' style='max-width:90%;' title='{image_name}'/></p>"
            )
            # 保存图片数据
            self.chat_panels["group"].chat_display.image_data[image_name] = {
                'data': image_data,
                'ext': image_ext
            }
                    
