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
    new_image_message = Signal(str, str, str, str, str, str, bool, str)  # 图片消息信号(username, ip, port, image_data, image_ext, timestamp, is_private, file_name)
    new_video_message = Signal(str, str, str, str, str, str, bool, str)  # 视频消息信号(username, ip, port, video_data, video_ext, timestamp, is_private, file_name)
    new_file_message = Signal(str, str, str, str, str, str, bool, str)  # 文件消息信号(username, ip, port, file_data, file_ext, timestamp, is_private, file_name)
    new_audio_message = Signal(str, str, str, str, str, str, bool, str)  # 音频消息信号(username, ip, port, audio_data, audio_ext, timestamp, is_private, file_name)
    
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
                  f"用户名: {self.username}")
            
            # 发送用登录信息到服务器
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
        
        # 发送连接失败信号时附带错误信息
        self.connection_failed.emit("连接已断开")
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
                
                # 分两步发送，确保数据完整性
                length_bytes = message_length.to_bytes(4, 'big')
                self.socket.sendall(length_bytes)
                self.socket.sendall(message_json.encode())
                
                print(f"\n[发送消息] 类型: {message.get('type')}")
                if message.get('type') in ['square_image', 'private_image']:
                    print("消息内容: [图片数据]")
                else:
                    print(f"消息内容: {message}")
            except Exception as e:
                print(f"[错误] 发送消息失败: {e}")
                self.stop()

    def receive_messages(self):
        """接收服务器消息的循环"""
        while self.socket:
            try:
                # 接收消息长度
                length_bytes = self.socket.recv(4)
                if not length_bytes:
                    print("[连接断开] 服务器关闭了连接")
                    break
                    
                message_length = int.from_bytes(length_bytes, 'big')
                
                # 分块接收消息
                chunks = []
                bytes_received = 0
                while bytes_received < message_length:
                    chunk = self.socket.recv(min(8192, message_length - bytes_received))
                    if not chunk:
                        raise ConnectionError("接收消息时连接断开")
                    chunks.append(chunk)
                    bytes_received += len(chunk)
                
                # 组合所有分块
                message_json = b''.join(chunks).decode()
                
                try:
                    message = json.loads(message_json)
                    # 处理接收到的消息
                    self.process_message(message)
                except json.JSONDecodeError as e:
                    print(f"[错误] JSON解析失败: {e}")
                    continue
                    
            except ConnectionError as e:
                print(f"[错误] 连接错误: {e}")
                break
            except Exception as e:
                print(f"[错误] 接收消息失败: {e}")
                break
        
        # 如果循环退出，说明连接已断开
        self.stop()

    def process_message(self, message):
        """处理接收到的消息"""
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
        elif message_type == 'square_image':
            self.handle_square_image(message)
        elif message_type == 'private_image':
            self.handle_private_image(message)
        elif message_type == 'square_video':
            self.handle_square_video(message)
        elif message_type == 'private_video':
            self.handle_private_video(message)
        elif message_type == 'square_file':
            self.handle_square_file(message)
        elif message_type == 'private_file':
            self.handle_private_file(message)
        elif message_type == 'square_audio':
            self.handle_square_audio(message)
        elif message_type == 'private_audio':
            self.handle_private_audio(message)

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

    def handle_square_image(self, message):
        """处理广场图片���息"""
        username = message.get('username')
        ip = message.get('ip')
        port = message.get('port')
        image_data = message.get('image_data')
        image_ext = message.get('image_ext')
        file_name = message.get('file_name')  # 获取文件名
        timestamp = message.get('timestamp')
        
        print(f"\n[收到广场图片消息]")
        print(f"发送者: {username} ({ip}:{port})")
        print(f"时间: {timestamp}")
        print(f"文件名: {file_name}")
        
        # 发送信号通知UI更新
        self.new_image_message.emit(username, ip, port, image_data, image_ext, timestamp, False, file_name)
    
    def handle_private_image(self, message):
        """处理私聊图片消息"""
        username = message.get('username')
        ip = message.get('ip')
        port = message.get('port')
        image_data = message.get('image_data')
        image_ext = message.get('image_ext')
        file_name = message.get('file_name')  # 获取文件名
        timestamp = message.get('timestamp')
        
        print(f"\n[收到私聊图片消息] {timestamp}")
        print(f"发送者: {username} ({ip}:{port})")
        print(f"文件名: {file_name}")
        
        # 发送信号通知UI更新
        self.new_image_message.emit(username, ip, str(port), image_data, image_ext, timestamp, True, file_name)

    def handle_square_video(self, message):
        """处理广场视频消息"""
        username = message.get('username')
        ip = message.get('ip')
        port = message.get('port')
        video_data = message.get('video_data')
        video_ext = message.get('video_ext')
        file_name = message.get('file_name')  # 获取文件名
        timestamp = message.get('timestamp')
        
        print(f"\n[收到广场视频消息]")
        print(f"发送者: {username} ({ip}:{port})")
        print(f"时间: {timestamp}")
        print(f"文件名: {file_name}")
        
        # 发送信号通知UI更新
        self.new_video_message.emit(username, ip, port, video_data, video_ext, timestamp, False, file_name)
    
    def handle_private_video(self, message):
        """处理私聊视频消息"""
        username = message.get('username')
        ip = message.get('ip')
        port = message.get('port')
        video_data = message.get('video_data')
        video_ext = message.get('video_ext')
        file_name = message.get('file_name')  # 获取文件名
        timestamp = message.get('timestamp')
        
        print(f"\n[收到私聊视频消息] {timestamp}")
        print(f"发送者: {username} ({ip}:{port})")
        print(f"文件名: {file_name}")
        
        # 发送信号通知UI更新
        self.new_video_message.emit(username, ip, str(port), video_data, video_ext, timestamp, True, file_name)

    def handle_square_file(self, message):
        """处理广场文件消息"""
        username = message.get('username')
        ip = message.get('ip')
        port = message.get('port')
        file_data = message.get('file_data')
        file_ext = message.get('file_ext')
        file_name = message.get('file_name')  # 获取文件名
        timestamp = message.get('timestamp')
        
        print(f"\n[收到广场文件消息]")
        print(f"发送者: {username} ({ip}:{port})")
        print(f"时间: {timestamp}")
        print(f"文件名: {file_name}")
        
        # 发送信号通知UI更新
        self.new_file_message.emit(username, ip, port, file_data, file_ext, timestamp, False, file_name)
    
    def handle_private_file(self, message):
        """处理私聊文件消息"""
        username = message.get('username')
        ip = message.get('ip')
        port = message.get('port')
        file_data = message.get('file_data')
        file_ext = message.get('file_ext')
        file_name = message.get('file_name')  # 获取文件名
        timestamp = message.get('timestamp')
        
        print(f"\n[收到私聊文件消息] {timestamp}")
        print(f"发送者: {username} ({ip}:{port})")
        print(f"文件名: {file_name}")
        
        # 发送信号通知UI更新
        self.new_file_message.emit(username, ip, str(port), file_data, file_ext, timestamp, True, file_name)

    def handle_square_audio(self, message):
        """处理广场音频消息"""
        username = message.get('username')
        ip = message.get('ip')
        port = message.get('port')
        audio_data = message.get('audio_data')
        audio_ext = message.get('audio_ext')
        file_name = message.get('file_name')  # 获取文件名
        timestamp = message.get('timestamp')
        
        print(f"\n[收到广场音频消息]")
        print(f"发送者: {username} ({ip}:{port})")
        print(f"时间: {timestamp}")
        print(f"文件名: {file_name}")
        
        # 发送信号通知UI更新
        self.new_audio_message.emit(username, ip, port, audio_data, audio_ext, timestamp, False, file_name)
    
    def handle_private_audio(self, message):
        """处理私聊音频消息"""
        username = message.get('username')
        ip = message.get('ip')
        port = message.get('port')
        audio_data = message.get('audio_data')
        audio_ext = message.get('audio_ext')
        file_name = message.get('file_name')  # 获取文件名
        timestamp = message.get('timestamp')
        
        print(f"\n[收到私聊音频消息] {timestamp}")
        print(f"发送者: {username} ({ip}:{port})")
        print(f"文件名: {file_name}")
        
        # 发送信号通知UI更新
        self.new_audio_message.emit(username, ip, str(port), audio_data, audio_ext, timestamp, True, file_name)

