import datetime
import socket
import json
import threading
from PySide6.QtCore import QObject, Signal
from datetime import datetime

class Client(QObject):
    # 定义信号用于UI更新
    connected = Signal()  # 连接成功信号
    connection_failed = Signal(str)  # 连接失败信号，携带错误信息
    new_user_login = Signal(str, str, int)  # 新用户登录信号(username, ip, port)
    old_friend_list = Signal(list)  # 已有用户列表信号，携带用户列表
    user_logout = Signal(str, str, int)  # 用户登出信号(username, ip, port)
    new_message = Signal(str, str, str, str, str)  # 群聊消息信号(username, ip, port, content, timestamp)
    new_private_message = Signal(str, str, str, str, str)  # 私聊消息信号(username, ip, port, content, timestamp)
    
    def __init__(self):
        super().__init__()
        # 初始化客户端属性
        self.socket = None        # 客户端socket连接
        self.username = ""        # 用户名
        self.server_ip = ""       # 服务器IP
        self.server_port = 0      # 服务器端口
        self.local_ip = ""        # 本地IP
        self.local_port = 0       # 本地端口

    def connect_to_server(self, server_ip, server_port, local_ip, local_port, username):
        """连接到服务器并初始化客户端"""
        try:
            # 保存连接参数
            self.server_ip = server_ip
            self.server_port = int(server_port)
            self.local_ip = local_ip
            self.local_port = int(local_port)
            self.username = username

            # 创建socket连接
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.bind((self.local_ip, self.local_port))
            self.socket.connect((self.server_ip, self.server_port))

            print(f"客户端启动成功。\n"
                  f"服务器地址：{self.server_ip}:{self.server_port}\n"
                  f"本地地址：{self.local_ip}:{self.local_port}\n"
                  f"用户名���{self.username}")
            
            # 发送用户登录信息到服务器
            self.send_login()
            
            # 启动消息接收线程
            self.receive_thread = threading.Thread(target=self.receive_messages)
            self.receive_thread.daemon = True  # 设置为守护线程
            self.receive_thread.start()
            
            # 发送连接成功信号，触发UI更新
            self.connected.emit()
            
        except Exception as e:
            print(f"连接失败: {e}")
            self.stop()

    def stop(self):
        """停止客户端连接"""
        print("\n[客户端关闭]")
        if hasattr(self, 'username') and self.username:
            print(f"用户名: {self.username}")
        if hasattr(self, 'local_ip') and self.local_ip:
            print(f"本地地址: {self.local_ip}:{self.local_port}")
        
        self.connection_failed.emit()
        if self.socket:
            try:
                self.socket.close()
                print("Socket连接已关闭")
            except Exception as e:
                print(f"[错误] 关闭Socket失败: {e}")
            self.socket = None

    def send_message(self, message):
        """发送消息到服务器"""
        if self.socket:
            try:
                message_json = json.dumps(message)
                message_length = len(message_json.encode())
                self.socket.send(message_length.to_bytes(4, 'big'))
                self.socket.send(message_json.encode())
                print(f"\n[发送消息] 类型: {message.get('type')}")
                print(f"消息内容: {message}")
            except Exception as e:
                print(f"[错误] 发送消息失败: {e}")

    def receive_messages(self):
        """接收服务器消息的循环"""
        while self.socket:
            try:
                # 接收消息长度
                length_bytes = self.socket.recv(4)
                if not length_bytes:
                    break
                message_length = int.from_bytes(length_bytes, 'big')
                
                # 接收消息内容
                message_json = self.socket.recv(message_length).decode()
                message = json.loads(message_json)
                
                # 处理接收到的消息
                self.process_message(message)
                
            except Exception as e:
                print(f"接收消息失败: {e}")
                break
        
        self.stop()

    def process_message(self, message):
        """处理接收到的消息
        Args:
            message: 接收到的消息字典
        """
        message_type = message.get('type')
        
        # 根据消息类型分发处理
        if message_type == 'new_friend_login':
            self.handle_new_friend_login(message)
        elif message_type == 'old_friend_list':
            self.handle_old_friend_list(message)
        elif message_type == 'one_user_logout':
            self.handle_user_logout(message)
        elif message_type == 'square_message':
            self.handle_square_message(message)
        elif message_type == 'private_message':
            self.handle_private_message(message)

    def send_login(self):
        """发送登录信息到服务器"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        login_info = {
            "type": "login",
            "username": self.username,
            "local_ip": self.local_ip,
            "local_port": self.local_port,
            "timestamp": timestamp
        }
        print(f"\n[发送登录请求] {timestamp}")
        print(f"用户名: {self.username}")
        print(f"本地地址: {self.local_ip}:{self.local_port}")
        self.send_message(login_info)

    def send_logout_info(self):
        """发送登出信息到服务器"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logout_info = {
            "type": "logout",
            "username": self.username,
            "local_ip": self.local_ip,
            "local_port": self.local_port,
            "timestamp": timestamp
        }
        print(f"\n[发送登出请求] {timestamp}")
        print(f"用户名: {self.username}")
        print(f"本地地址: {self.local_ip}:{self.local_port}")
        self.send_message(logout_info)

    def handle_new_friend_login(self, message):
        """处理新朋友登录消息"""
        username = message.get('username')
        local_ip = message.get('local_ip')
        local_port = int(message.get('local_port'))
        timestamp = message.get('timestamp')
        
        print(f"\n[新用户上线] {timestamp}")
        print(f"用户名: {username}")
        print(f"地址: {local_ip}:{local_port}")
        
        # 发送信号通知UI更新
        self.new_user_login.emit(username, local_ip, local_port)

    def handle_old_friend_list(self, message):
        """处理已有用户列表消息"""
        users = message.get('users', [])
        timestamp = message.get('timestamp')
        
        print(f"\n[收到用户列表] {timestamp}")
        print(f"在线用户数: {len(users)}人")
        for user in users:
            username = user.get('username')
            address = user.get('address')
            if isinstance(address, (list, tuple)) and len(address) >= 2:
                ip, port = address
                print(f"- {username} ({ip}:{port})")
        
        # 发送信号通知UI更新
        self.old_friend_list.emit(users)

    def handle_user_logout(self, message):
        """处理用户登出消息"""
        username = message.get('username')
        local_ip = message.get('local_ip')
        local_port = int(message.get('local_port'))
        timestamp = message.get('timestamp')
        
        print(f"\n[用户离线] {timestamp}")
        print(f"用户名: {username}")
        print(f"地址: {local_ip}:{local_port}")
        
        # 发送信号通知UI更新
        self.user_logout.emit(username, local_ip, local_port)

    def handle_square_message(self, message):
        """处理广场消息"""
        username = message.get('username')
        ip = message.get('ip')
        port = message.get('port')
        content = message.get('content')
        timestamp = message.get('timestamp')
        
        print(f"\n[收到广场消息]")
        print(f"发送者: {username} ({ip}:{port})")
        print(f"内容: {content}")
        print(f"时间: {timestamp}")
        
        # 发送信号通知UI更新
        self.new_message.emit(username, ip, port, content, timestamp)
    
    def handle_private_message(self, message):
        """处理私聊消息"""
        username = message.get('username')
        ip = message.get('ip')
        port = message.get('port')
        content = message.get('content')
        timestamp = message.get('timestamp')
        
        print(f"\n[收到私聊消息] {timestamp}")
        print(f"发送者: {username} ({ip}:{port})")
        print(f"内容: {content}")
        
        # 发送信号通知UI更新
        self.new_private_message.emit(username, ip, str(port), content, timestamp)

