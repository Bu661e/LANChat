from server import ChatServer
import signal
import sys

def signal_handler(sig, frame):
    print("\n收到 Ctrl+C 信号，准备关闭服务器...")
    if server:
        server.stop()
    sys.exit(0)

if __name__ == '__main__':
    # 注册信号处理函数
    signal.signal(signal.SIGINT, signal_handler)
    
    # 创建并启动服务器
    server = ChatServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n收到 Ctrl+C 信号，准备关闭服务器...")
        server.stop()