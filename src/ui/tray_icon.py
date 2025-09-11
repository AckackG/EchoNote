#!/user/bin-env python3
# -*- coding: utf-8 -*-
import os
import sys
import threading
import pystray
from PIL import Image
from loguru import logger


class TrayIconManager:
    def __init__(self, app):
        self.app = app
        self.tray_icon = None

    def show_window(self, icon, item):
        """从系统托盘恢复窗口"""
        icon.stop()
        self.tray_icon = None
        self.app.after(0, self.app.deiconify)

    def setup_tray_icon(self):
        """创建并运行系统托盘图标"""
        if self.tray_icon and self.tray_icon.visible:
            return

        # --- 修改的核心逻辑 ---
        # 判断当前是在开发环境还是在打包后的环境中
        if getattr(sys, "frozen", False):
            # 如果是打包后的环境 (sys.frozen = True)
            # PyInstaller 会将资源解压到 sys._MEIPASS 指定的临时目录
            base_path = sys._MEIPASS
            # 我们的 icon.png 被打包到了根目录，所以直接拼接
            icon_path = os.path.join(base_path, "icon.png")
        else:
            # 如果是开发环境
            # 路径相对于当前文件 (tray_icon.py)
            base_path = os.path.dirname(os.path.abspath(__file__))
            # icon.png 在 src 目录下，即 ui 目录的上一级
            icon_path = os.path.join(base_path, "..", "icon.png")
        # --- 修改结束 ---

        try:
            logger.info(f"正在从以下路径加载托盘图标: {icon_path}")
            image = Image.open(icon_path)
        except Exception as e:
            logger.warning(
                f"图标文件 '{icon_path}' 未找到或加载失败, 将使用默认图标。错误: {e}"
            )
            image = Image.new("RGB", (64, 64), "blue")

        menu = (
            pystray.MenuItem("显示窗口", self.show_window, default=True),
            pystray.MenuItem("退出", self.app.quit_app_from_tray),
        )

        self.tray_icon = pystray.Icon("Echonote", image, "Echonote", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
