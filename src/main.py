#!/user/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys  # 导入 sys 模块

import customtkinter as ctk
from loguru import logger

# 导入我们自己的模块
from config_manager import ConfigManager
from note_manager import NoteManager
from scheduler_service import SchedulerService
from ui.app_main import App

# --- 全局配置 ---
ctk.set_appearance_mode("System")  # Modes: "System" (default), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (default), "green", "dark-blue"

# --- 日志配置 ---
# 判断程序是否被打包（例如被PyInstaller打包）
if getattr(sys, 'frozen', False):
    # 如果是打包后的 exe，则基准路径是 exe 文件所在的目录
    base_path = os.path.dirname(sys.executable)
else:
    # 如果是直接运行的 .py 脚本，则基准路径是项目根目录（src的上级）
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

log_path = os.path.join(base_path, 'logs', 'app.log')
# 如果日志目录不存在，则创建它
os.makedirs(os.path.dirname(log_path), exist_ok=True)
logger.add(log_path, rotation="10 MB", retention="7 days", encoding="utf-8", level="INFO")

if __name__ == "__main__":
    logger.info("应用程序启动...")

    # 初始化核心组件
    config = ConfigManager(config_path='config.json')
    notes = NoteManager(config.get_setting('data_folder'))
    scheduler = SchedulerService(config, notes)

    # 启动后台调度服务
    scheduler.start()

    # 创建并运行GUI
    app = App(config, notes, scheduler)
    app.mainloop()
