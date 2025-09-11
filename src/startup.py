#!/user/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import winshell
from loguru import logger


def get_startup_folder():
    """获取Windows启动文件夹路径"""
    return os.path.join(winshell.startup())


def get_shortcut_path():
    """获取将在启动文件夹中创建的快捷方式的完整路径"""
    startup_folder = get_startup_folder()
    # 注意：这里我们为快捷方式命名，确保它不会太通用
    return os.path.join(startup_folder, "EchoNote.lnk")


def set_autostart(enable: bool):
    """
    设置或取消开机自启
    :param enable: True表示设置，False表示取消
    """
    shortcut_path = get_shortcut_path()

    # 获取可执行文件的路径，兼容打包后的exe和直接运行的py脚本
    if getattr(sys, "frozen", False):
        # 如果是打包后的 exe
        executable_path = sys.executable
    else:
        # 如果是直接运行的 .py 脚本
        # 我们需要 pythonw.exe 来无窗口后台启动
        pythonw_path = sys.executable.replace("python.exe", "pythonw.exe")
        script_path = os.path.abspath(sys.argv[0])
        executable_path = f'"{pythonw_path}" "{script_path}"'

    if enable:
        if not os.path.exists(shortcut_path):
            try:
                # winshell.shortcut需要可执行文件路径作为参数
                # 对于脚本，我们直接创建快捷方式并设置其目标和参数
                if getattr(sys, "frozen", False):
                    with winshell.shortcut(shortcut_path) as shortcut:
                        shortcut.path = executable_path
                        shortcut.working_directory = os.path.dirname(executable_path)
                        shortcut.description = "Periodic Information Reminder"
                else:
                    # 对于脚本，需要更手动的方式
                    # 此处简化处理，直接调用winshell创建
                    logger.warning(
                        "在开发模式下创建自启快捷方式可能不准确，推荐在打包后使用。"
                    )
                    with winshell.shortcut(shortcut_path) as shortcut:
                        shortcut.path = sys.executable.replace(
                            "python.exe", "pythonw.exe"
                        )
                        shortcut.arguments = f'"{os.path.abspath(sys.argv[0])}"'
                        shortcut.working_directory = os.path.dirname(
                            os.path.abspath(sys.argv[0])
                        )
                        shortcut.description = "Periodic Information Reminder"

                logger.info("已设置开机自启。")
            except Exception as e:
                logger.error(f"设置开机自启失败: {e}")
        else:
            logger.info("开机自启已设置。")
    else:
        if os.path.exists(shortcut_path):
            try:
                os.remove(shortcut_path)
                logger.info("已取消开机自启。")
            except Exception as e:
                logger.error(f"取消开机自启失败: {e}")
        else:
            logger.info("开机自启未设置，无需取消。")


def is_autostart_enabled():
    """检查当前是否已设置开机自启"""
    return os.path.exists(get_shortcut_path())
