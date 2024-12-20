import socket
import json
import threading
from datetime import datetime

class ChatServer:
    def __init__(self):
        # 初始化服务器属性
        self.host = ''           # 服务器主机地址
        self.port = 0           # 服务器端口
        self.server_socket = None  # 服务器socket对象
        self.clients = {}       # 存储客户端信息 {client_socket: {'username': str, 'address': tuple}}
        self.running = False    # 服务器运行状态

    def start(self, host='172.20.10.4', port=8000):
        """启动服务器并开始监听连接"""
        try:
            # 初始化服务器配置
            self.host = host
            self.port = port

            # 创建并配置服务器socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 允许地址重用
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)  # 最大连接数为5
            self.running = True

            print(f"服务器启动成功 - {self.host}:{self.port}")
            self.accept_connections()  # 开始接受客户端连接
            
        except KeyboardInterrupt:
            print("\n正在关闭服务器...")
            self.stop()
        except Exception as e:
            print(f"服务器启动失败: {e}")
            self.stop()

    def accept_connections(self):
        """接受客户端连接的主循环"""
        while self.running:
            try:
                # 设置accept超时，以便定期检查running状态
                self.server_socket.settimeout(1.0)
                try:
                    client_socket, address = self.server_socket.accept()
                    print(f"新的连接: {address}")
                    
                    # 为每个客户端创建独立的处理线程
                    client_thread = threading.Thread(
                        target=self.receive_messages,
                        args=(client_socket, address)
                    )
                    client_thread.daemon = True  # 设置为守护线程
                    client_thread.start()
                    
                except socket.timeout:
                    continue  # 超时后继续循环
                    
            except KeyboardInterrupt:
                print("\n正在关闭服务器...")
                break
            except Exception as e:
                if self.running:
                    print(f"接受连接失败: {e}")
                break
        
        self.stop()  # 确保服务器正确关闭

    def stop(self):
        """停止服务器"""
        self.running = False
        
        # 断开所有客户端连接
        for client_socket in list(self.clients.keys()):
            try:
                client_socket.close()
            except:
                pass
        self.clients.clear()
        
        # 关闭服务器socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None
            
        print("服务器已关闭")
    
    def send_message(self, client_socket, message):
        """发送消息到客户端"""
        if client_socket:
            try:
                # 将消息转换为JSON字符串
                message_json = json.dumps(message, ensure_ascii=False)
                # 发送消息长度
                message_length = len(message_json.encode())
                client_socket.sendall(message_length.to_bytes(4, 'big'))
                # 发送消息内容
                client_socket.sendall(message_json.encode())
                
                print(f"\n[发送消息]")
                if client_socket in self.clients:
                    target = self.clients[client_socket]
                    print(f"目标用户: {target['username']} ({target['address'][0]}:{target['address'][1]})")
                print(f"消息类型: {message.get('type')}")
                if message.get('type') in ['square_image', 'private_image']:
                    print("消息内容: [图片数据]")
                else:
                    print(f"消息内容: {message}")
                
            except Exception as e:
                print(f"[错误] 发送消息失败: {e}")
                if client_socket in self.clients:
                    target = self.clients[client_socket]
                    print(f"目标用户: {target['username']} ({target['address'][0]}:{target['address'][1]})")
                # 如果发送失败，关闭连接
                self.handle_logout(client_socket)

    def receive_messages(self, client_socket, address):
        """接收并处理客户端消息"""
        try:
            print(f"\n[新连接] 地址: {address}")
            while self.running:
                try:
                    # 接收消息长度
                    length_bytes = client_socket.recv(4)
                    if not length_bytes:
                        print(f"[连接断开] 客户端主动断开连接")
                        break
                        
                    message_length = int.from_bytes(length_bytes, 'big')
                    
                    # 分块接收大消息
                    chunks = []
                    bytes_received = 0
                    while bytes_received < message_length:
                        chunk = client_socket.recv(min(8192, message_length - bytes_received))
                        if not chunk:
                            raise ConnectionError("接收消息时连接断开")
                        chunks.append(chunk)
                        bytes_received += len(chunk)
                    
                    # 组合所有分块
                    message_json = b''.join(chunks).decode()
                    
                    try:
                        message = json.loads(message_json)
                        print(f"\n[收到消息] 类型: {message.get('type')}")
                        if message.get('type') in ['square_image', 'private_image']:
                            print("消息内容: [图片数据]")
                        else:
                            print(f"消息内容: {message}")
                        
                        # 处理��息
                        self.process_message(client_socket, message)
                    except json.JSONDecodeError as e:
                        print(f"[错误] JSON解析失败: {e}")
                        print(f"原始消息: {message_json[:200]}...")  # 只打印前200个字符
                        continue
                        
                except ConnectionResetError:
                    print(f"[错误] 客户端异常断开连接")
                    break
                except Exception as e:
                    print(f"[错误] 接收消息时发生错误: {e}")
                    break
                    
        except Exception as e:
            if client_socket in self.clients:
                user_info = self.clients[client_socket]
                print(f"[错误] 处理客户端消息失败: {e}")
                print(f"用户信息: {user_info['username']} ({user_info['address'][0]}:{user_info['address'][1]})")
        finally:
            self.handle_logout(client_socket)

    def process_message(self, client_socket, message):
        """处理客户端消息"""
        message_type = message.get('type')
        
        if message_type == 'login':
            self.handle_login(client_socket, message)
        elif message_type == 'square_message':
            self.handle_square_message(client_socket, message)
        elif message_type == 'private_message':
            self.handle_private_message(client_socket, message)
        elif message_type == 'square_image':
            self.handle_square_image(client_socket, message)
        elif message_type == 'private_image':
            self.handle_private_image(client_socket, message)
        elif message_type == 'square_video':
            self.handle_square_video(client_socket, message)
        elif message_type == 'private_video':
            self.handle_private_video(client_socket, message)
        elif message_type == 'square_file':
            self.handle_square_file(client_socket, message)
        elif message_type == 'private_file':
            self.handle_private_file(client_socket, message)
        elif message_type == 'square_audio':
            self.handle_square_audio(client_socket, message)
        elif message_type == 'private_audio':
            self.handle_private_audio(client_socket, message)
        elif message_type == 'logout':
            self.handle_logout(client_socket)

    def handle_login(self, client_socket, message):
        """处理登录消息"""
        username = message.get('username')
        local_ip = message.get('local_ip')
        local_port = message.get('local_port')
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"\n[用户登录] {timestamp}")
        print(f"用户名: {username}")
        print(f"地址: {local_ip}:{local_port}")
        
        # 保存客户端信息
        self.clients[client_socket] = {
            'username': username,
            'address': (local_ip, local_port)
        }
        
        print(f"当前在线用户: {len(self.clients)}人")
        for sock, info in self.clients.items():
            print(f"- {info['username']} ({info['address'][0]}:{info['address'][1]})")

        # 向新用户发送当前用户列表
        users = []  # 得到所有用户，包括自己
        for c, info in self.clients.items():
            users.append({
                'username': info['username'],
                'address': info['address']
            })
        
        print(f"发送给新用户的用户列表: {users}")

        try:
            self.send_message(client_socket, {
                'type': 'old_friend_list',
                'users': users,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        except Exception as e:
            print(f"向新用户发送当前用户列表消息失败: {e}")

        # 向老用户广播新用户上线消息
        for c in list(self.clients.keys()):
            if c == client_socket:  # 排除自己
                continue
            try:
                self.send_message(c, {
                    'type': 'new_friend_login',
                    'username': username,
                    'local_ip': local_ip,
                    'local_port': local_port,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
            except Exception as e:
                print(f"向老用户发送新用户登录消息失败: {e}")
        
    def handle_square_message(self, client_socket, message):
        """处理广场消息"""
        if client_socket not in self.clients:
            return
        
        sender = self.clients[client_socket]
        username = sender['username']
        ip, port = sender['address']
        content = message.get('content')
        timestamp = message.get('timestamp')
        
        print(f"\n[广场消息] {timestamp}")
        print(f"发送者: {username} ({ip}:{port})")
        print(f"内容: {content}")
        
        # 广播消息给所有用户
        broadcast_message = {
            'type': 'square_message',
            'username': username,
            'ip': ip,
            'port': port,
            'content': content,
            'timestamp': timestamp
        }
        
        # 广播给所有用户（除了发送者）
        broadcast_count = 0
        for c in list(self.clients.keys()):
            if c != client_socket:
                try:
                    self.send_message(c, broadcast_message)
                    broadcast_count += 1
                except Exception as e:
                    print(f"[错误] 向 {self.clients[c]['username']} 发送消息失败: {e}")
        
        print(f"消息已广播给 {broadcast_count} 个用户")
    # 1.3 logout
    def handle_logout(self, client_socket):
        """处理登出消息"""
        if client_socket in self.clients:
            # 获取用户信息
            user_info = self.clients[client_socket]
            username = user_info['username']
            local_ip, local_port = user_info['address']
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"\n[用户登出] {timestamp}")
            print(f"用户名: {username}")
            print(f"地址: {local_ip}:{local_port}")
            
            # 向其他用户广播该用户登出消息
            logout_message = {
                'type': 'one_user_logout',
                'username': username,
                'local_ip': local_ip,
                'local_port': local_port,
                'timestamp': timestamp
            }
            
            # 广播登出消息
            broadcast_count = 0
            for c in list(self.clients.keys()):
                if c != client_socket:
                    try:
                        self.send_message(c, logout_message)
                        broadcast_count += 1
                    except Exception as e:
                        print(f"[错误] 向 {self.clients[c]['username']} 发送登出消息失败: {e}")
            
            # 移除客户端
            client_socket.close()
            del self.clients[client_socket]
            
            print(f"登出消息已广播给 {broadcast_count} 个用户")
            print(f"当前在线用户: {len(self.clients)}人")
            for sock, info in self.clients.items():
                print(f"- {info['username']} ({info['address'][0]}:{info['address'][1]})")

    def handle_private_message(self, client_socket, message):
        """处理私聊消息"""
        if client_socket not in self.clients:
            return
        
        sender = self.clients[client_socket]
        username = sender['username']
        sender_ip, sender_port = sender['address']
        
        target_ip = message.get('target_ip')
        target_port = int(message.get('target_port'))
        content = message.get('content')
        timestamp = message.get('timestamp')
        
        print(f"\n处理私聊消息:")
        print(f"发送者: {username} ({sender_ip}:{sender_port})")
        print(f"目标地址: {target_ip}:{target_port}")
        print(f"当前在线用户: {self.clients}")
        
        # 查找目标用户的socket
        target_socket = None
        for sock, info in self.clients.items():
            if (info['address'][0] == target_ip and 
                info['address'][1] == int(target_port)):  # 确保端口号也匹配
                target_socket = sock
                print(f"找到目标用户: {info['username']}")
                break
        
        if target_socket:
            try:
                # 发送私聊消息给目标用户
                self.send_message(target_socket, {
                    'type': 'private_message',
                    'username': username,
                    'ip': sender_ip,
                    'port': sender_port,
                    'content': content,
                    'timestamp': timestamp
                })
                print(f"私聊消息发送成功")
            except Exception as e:
                print(f"发送私聊消息失败: {e}")
        else:
            print(f"未找到目标用户")

    def send_private_message(self, from_user, to_user, message):
        """发送私聊消息"""
        # 找到目标用户的socket
        target_socket = None
        for client_socket, client_info in self.clients.items():
            if client_info['username'] == to_user:
                target_socket = client_socket
                break
                
        if target_socket:
            try:
                message_json = json.dumps(message)
                message_length = len(message_json.encode())
                target_socket.send(message_length.to_bytes(4, 'big'))
                target_socket.send(message_json.encode())
            except Exception as e:
                print(f"发送私聊消息失败: {e}")
                self.remove_client(target_socket) 

    def handle_square_image(self, client_socket, message):
        """处理广场图片消息"""
        if client_socket not in self.clients:
            return
        
        sender = self.clients[client_socket]
        username = sender['username']
        ip, port = sender['address']
        image_data = message.get('image_data')
        image_ext = message.get('image_ext')
        file_name = message.get('file_name')  # 获取文件名
        timestamp = message.get('timestamp')
        
        print(f"\n[广场图片消息] {timestamp}")
        print(f"发送者: {username} ({ip}:{port})")
        print(f"文件名: {file_name}")
        
        # 广播消息给所有用户
        broadcast_message = {
            'type': 'square_image',
            'username': username,
            'ip': ip,
            'port': port,
            'image_data': image_data,
            'image_ext': image_ext,
            'file_name': file_name,  # 添加文件名
            'timestamp': timestamp
        }
        
        # 广播给所有用户（除了发送者）
        for c in list(self.clients.keys()):
            if c != client_socket:
                try:
                    self.send_message(c, broadcast_message)
                except Exception as e:
                    print(f"向用户发送广场图片消息失败: {e}")
                    
    def handle_private_image(self, client_socket, message):
        """处理私聊图片消息"""
        if client_socket not in self.clients:
            return
            
        sender = self.clients[client_socket]
        username = sender['username']
        ip, port = sender['address']
        target_ip = message.get('target_ip')
        target_port = message.get('target_port')
        image_data = message.get('image_data')
        image_ext = message.get('image_ext')
        file_name = message.get('file_name')  # 获取文件名
        timestamp = message.get('timestamp')
        
        print(f"\n[私聊图片消息] {timestamp}")
        print(f"发送者: {username} ({ip}:{port})")
        print(f"接收者: {target_ip}:{target_port}")
        print(f"文件名: {file_name}")
        
        # 查找目标客户端
        target_client = None
        for c, info in self.clients.items():
            if info['address'] == (target_ip, int(target_port)):
                target_client = c
                break
                
        if target_client:
            try:
                self.send_message(target_client, {
                    'type': 'private_image',
                    'username': username,
                    'ip': ip,
                    'port': port,
                    'image_data': image_data,
                    'image_ext': image_ext,
                    'file_name': file_name,  # 添加文件名
                    'timestamp': timestamp
                })
            except Exception as e:
                print(f"发送私聊图片消息失败: {e}")

    def handle_square_video(self, client_socket, message):
        """处理广场视频消息"""
        if client_socket not in self.clients:
            return
        
        sender = self.clients[client_socket]
        username = sender['username']
        ip, port = sender['address']
        video_data = message.get('video_data')
        video_ext = message.get('video_ext')
        file_name = message.get('file_name')  # 获取文件名
        timestamp = message.get('timestamp')
        
        print(f"\n[广场视频消息] {timestamp}")
        print(f"发送者: {username} ({ip}:{port})")
        print(f"文件名: {file_name}")
        
        # 广播消息给所有用户
        broadcast_message = {
            'type': 'square_video',
            'username': username,
            'ip': ip,
            'port': port,
            'video_data': video_data,
            'video_ext': video_ext,
            'file_name': file_name,  # 添加文件名
            'timestamp': timestamp
        }
        
        # 广播给所有用户（除了发送者）
        for c in list(self.clients.keys()):
            if c != client_socket:
                try:
                    self.send_message(c, broadcast_message)
                except Exception as e:
                    print(f"向用户发送广场视频消息失败: {e}")
                    
    def handle_private_video(self, client_socket, message):
        """处理私聊视频消息"""
        if client_socket not in self.clients:
            return
            
        sender = self.clients[client_socket]
        username = sender['username']
        ip, port = sender['address']
        target_ip = message.get('target_ip')
        target_port = message.get('target_port')
        video_data = message.get('video_data')
        video_ext = message.get('video_ext')
        file_name = message.get('file_name')  # 获取文件名
        timestamp = message.get('timestamp')
        
        print(f"\n[私聊视频消息] {timestamp}")
        print(f"发送者: {username} ({ip}:{port})")
        print(f"接收者: {target_ip}:{target_port}")
        print(f"文件名: {file_name}")
        
        # 查找目标客户端
        target_client = None
        for c, info in self.clients.items():
            if info['address'] == (target_ip, int(target_port)):
                target_client = c
                break
                
        if target_client:
            try:
                self.send_message(target_client, {
                    'type': 'private_video',
                    'username': username,
                    'ip': ip,
                    'port': port,
                    'video_data': video_data,
                    'video_ext': video_ext,
                    'file_name': file_name,  # 添加文件名
                    'timestamp': timestamp
                })
            except Exception as e:
                print(f"��送私聊视频消息失败: {e}")

    def handle_square_file(self, client_socket, message):
        """处理广场文件消息"""
        if client_socket not in self.clients:
            return
        
        sender = self.clients[client_socket]
        username = sender['username']
        ip, port = sender['address']
        file_data = message.get('file_data')
        file_ext = message.get('file_ext')
        file_name = message.get('file_name')  # 获取文件名
        timestamp = message.get('timestamp')
        
        print(f"\n[广场文件消息] {timestamp}")
        print(f"发送者: {username} ({ip}:{port})")
        print(f"文件名: {file_name}")
        
        # 广播消息给所有用户
        broadcast_message = {
            'type': 'square_file',
            'username': username,
            'ip': ip,
            'port': port,
            'file_data': file_data,
            'file_ext': file_ext,
            'file_name': file_name,  # 添加文件名
            'timestamp': timestamp
        }
        
        # 广播给所有用户（除了发送者）
        for c in list(self.clients.keys()):
            if c != client_socket:
                try:
                    self.send_message(c, broadcast_message)
                except Exception as e:
                    print(f"向用户发送广场文件消息失败: {e}")
                    
    def handle_private_file(self, client_socket, message):
        """处理私聊文件消息"""
        if client_socket not in self.clients:
            return
            
        sender = self.clients[client_socket]
        username = sender['username']
        ip, port = sender['address']
        target_ip = message.get('target_ip')
        target_port = message.get('target_port')
        file_data = message.get('file_data')
        file_ext = message.get('file_ext')
        file_name = message.get('file_name')  # 获取文件名
        timestamp = message.get('timestamp')
        
        print(f"\n[私聊文件消息] {timestamp}")
        print(f"发送者: {username} ({ip}:{port})")
        print(f"接收者: {target_ip}:{target_port}")
        print(f"文件名: {file_name}")
        
        # 查找目标客户端
        target_client = None
        for c, info in self.clients.items():
            if info['address'] == (target_ip, int(target_port)):
                target_client = c
                break
                
        if target_client:
            try:
                self.send_message(target_client, {
                    'type': 'private_file',
                    'username': username,
                    'ip': ip,
                    'port': port,
                    'file_data': file_data,
                    'file_ext': file_ext,
                    'file_name': file_name,  # 添加文件名
                    'timestamp': timestamp
                })
            except Exception as e:
                print(f"发送私聊文件消息失败: {e}")

    def handle_square_audio(self, client_socket, message):
        """处理广场音频消息"""
        if client_socket not in self.clients:
            return
        
        sender = self.clients[client_socket]
        username = sender['username']
        ip, port = sender['address']
        audio_data = message.get('audio_data')
        audio_ext = message.get('audio_ext')
        file_name = message.get('file_name')  # 获取文件名
        timestamp = message.get('timestamp')
        
        print(f"\n[广场音频消息] {timestamp}")
        print(f"发送者: {username} ({ip}:{port})")
        print(f"文件名: {file_name}")
        
        # 广播消息给所有用户
        broadcast_message = {
            'type': 'square_audio',
            'username': username,
            'ip': ip,
            'port': port,
            'audio_data': audio_data,
            'audio_ext': audio_ext,
            'file_name': file_name,  # 添加���件名
            'timestamp': timestamp
        }
        
        # 广播给所有用户（除了发送者）
        for c in list(self.clients.keys()):
            if c != client_socket:
                try:
                    self.send_message(c, broadcast_message)
                except Exception as e:
                    print(f"向用户发送广场音频消息失败: {e}")
                    
    def handle_private_audio(self, client_socket, message):
        """处理私聊音频消息"""
        if client_socket not in self.clients:
            return
            
        sender = self.clients[client_socket]
        username = sender['username']
        ip, port = sender['address']
        target_ip = message.get('target_ip')
        target_port = message.get('target_port')
        audio_data = message.get('audio_data')
        audio_ext = message.get('audio_ext')
        file_name = message.get('file_name')  # 获取文件名
        timestamp = message.get('timestamp')
        
        print(f"\n[私聊音频消息] {timestamp}")
        print(f"发送者: {username} ({ip}:{port})")
        print(f"接收者: {target_ip}:{target_port}")
        print(f"文件名: {file_name}")
        
        # 查找目标客户端
        target_client = None
        for c, info in self.clients.items():
            if info['address'] == (target_ip, int(target_port)):
                target_client = c
                break
                
        if target_client:
            try:
                self.send_message(target_client, {
                    'type': 'private_audio',
                    'username': username,
                    'ip': ip,
                    'port': port,
                    'audio_data': audio_data,
                    'audio_ext': audio_ext,
                    'file_name': file_name,  # 添加文件名
                    'timestamp': timestamp
                })
            except Exception as e:
                print(f"发送私聊音频消息失败: {e}")