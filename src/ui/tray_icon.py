#!/user/bin/env python3
# -*- coding: utf-8 -*-
#!/user/bin/env python3
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

        try:
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            # The icon is in the root directory, so we go up one level from the 'ui' directory
            icon_path = os.path.join(base_path, '..', 'icon.png')
            image = Image.open(icon_path)
        except Exception:
            logger.warning(f"图标文件 'icon.png' 未找到, 将使用默认图标。")
            image = Image.new('RGB', (64, 64), 'blue')

        menu = (pystray.MenuItem('显示窗口', self.show_window, default=True),
                pystray.MenuItem('退出', self.app.quit_app_from_tray))

        self.tray_icon = pystray.Icon("TFInformer", image, "TFInformer", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()