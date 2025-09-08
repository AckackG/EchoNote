#!/user/bin/env python3
# -*- coding: utf-8 -*-
import os
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
log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs', 'app.log')
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