import sys
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PySide6.QtGui import QPixmap
import os

# 如果你使用的是 PyQt6，请将 PyQt5 替换为 PyQt6

class ImageWidget(QWidget):
    def __init__(self):
        super().__init__()

        # 创建一个 QLabel 用于显示图片
        self.label = QLabel(self)

        # 加载图片
        # 获取当前脚本的绝对路径
        current_file_path = os.path.abspath(__file__)

        # 获取当前脚本所在的目录
        current_directory = os.path.dirname(current_file_path)

        # 定义图片名称
        image_name = 'QQ.png'

        # 拼接图片的完整路径
        image_path = os.path.join(current_directory, image_name)

        pixmap = QPixmap(image_path)  # 替换为你的图片路径

        # 如果图片太大，可以调整大小
        pixmap = pixmap.scaled(300, 300)  # 调整为 300x300 像素

        # 构建 HTML 格式的字符串
        html_content = f"""
        <p>这是第一段文字。</p>
        <img src="{image_path}" width="100" height="100" alt="图片">
        <p>这是第二段文字。</p>
        """

        # 将 HTML 内容设置到 QLabel 上
        self.label.setText(html_content)



        # 设置布局
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        # 设置窗口标题和大小
        self.setWindowTitle("显示图片")
        self.resize(400, 400)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ImageWidget()
    window.show()
    sys.exit(app.exec_())