### 基于Python和PySide6的局域网在线聊天室
`server`下的是服务端代码
- 在`server.py`的`Server`类的构造函数更改服务端的配置

`client`下的是客户端代码，需要安装PySide6
- `config.json`中可以更改默认用户配置

`info_example.txt`中是CS之间传递的消息格式

#### 用法：

```
cd server
python main.py
```

```
cd client
python main.py
```