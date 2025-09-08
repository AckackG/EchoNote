#!/user/bin/env python3
# -*- coding: utf-8 -*-
import schedule
import time
import threading
import os
import subprocess
from loguru import logger
from win10toast_click import ToastNotifier


class MyToastNotifier(ToastNotifier):
    def __init__(self):
        super().__init__()

    def on_destroy(self, hwnd, msg, wparam, lparam):
        super().on_destroy(hwnd, msg, wparam, lparam)
        return 0


class SchedulerService:
    def __init__(self, config_manager, note_manager):
        self.config_manager = config_manager
        self.note_manager = note_manager
        self.stop_event = threading.Event()
        self.thread = None
        self.toaster = MyToastNotifier()

    def _run_continuously(self):
        """后台线程持续运行schedule任务"""
        logger.info("调度服务已启动。")
        while not self.stop_event.is_set():
            schedule.run_pending()
            time.sleep(1)
        logger.info("调度服务已停止。")

    def start(self):
        """启动调度服务线程"""
        if self.thread is None or not self.thread.is_alive():
            self.stop_event.clear()
            self.thread = threading.Thread(target=self._run_continuously, daemon=True)
            self.thread.start()
            self.reload_schedules()

    def stop(self):
        """停止调度服务线程"""
        self.stop_event.set()
        if self.thread:
            self.thread.join()  # 等待线程结束

    def reload_schedules(self):
        """清空并重新加载所有笔记的调度任务"""
        schedule.clear()
        logger.info("正在重新加载所有调度任务...")
        all_schedules = self.config_manager.config.get('notes_schedule', {})

        for filename, schedule_info in all_schedules.items():
            try:
                schedule_rules = schedule_info.get("schedule")
                mode = schedule_info.get("mode")
                if not schedule_rules or not mode:
                    continue

                # **--- 修改开始 ---**
                # 检查任务规则是单个字符串还是列表（针对多选星期）
                # 并将其统一处理为列表
                if isinstance(schedule_rules, str):
                    rules_to_process = [schedule_rules]
                elif isinstance(schedule_rules, list):
                    rules_to_process = schedule_rules
                else:
                    logger.warning(f"为 '{filename}' 跳过无效的调度规则格式: {schedule_rules}")
                    continue

                # 遍历所有规则并创建任务
                for rule_str in rules_to_process:
                    if not rule_str: continue  # 跳过空规则
                    job = eval(f"schedule.{rule_str}")
                    job.do(self.trigger_reminder, filename=filename, mode=mode)
                    logger.info(f"已为 '{filename}' 添加任务: {rule_str}, 模式: {mode}")
                # **--- 修改结束 ---**

            except Exception as e:
                logger.error(f"为 '{filename}' 添加任务失败，配置: '{schedule_info}'. 错误: {e}")

        logger.info(f"重新加载完成，当前共有 {len(schedule.get_jobs())} 个任务。")

    def trigger_reminder(self, filename, mode):
        """根据模式触发提醒"""
        logger.info(f"触发提醒: 文件='{filename}', 模式='{mode}'")
        data_folder = self.config_manager.get_setting("data_folder")
        if not data_folder:
            logger.error("无法触发提醒，因为数据文件夹未设置。")
            return

        file_path = os.path.join(data_folder, filename)
        if not os.path.exists(file_path):
            logger.error(f"无法触发提醒，文件不存在: {file_path}")
            return

        if mode == 'light':
            self.show_light_reminder(filename, file_path)
        elif mode == 'popup':
            self.show_popup_reminder(filename, file_path)

    def show_light_reminder(self, filename, file_path):
        """显示轻度提醒 (Toast)"""
        try:
            # 使用 win10toast-click，可以传入一个点击后的回调函数
            self.toaster.show_toast(
                title="笔记提醒",
                msg=f"是时候回顾一下笔记了：\n{filename}",
                duration=10,
                threaded=True,
                callback_on_click=lambda: self.open_file_with_editor(filename, file_path)
            )
            logger.info(f"已发送系统通知 for '{filename}'")
        except Exception as e:
            logger.error(f"发送系统通知失败: {e}")

    def show_popup_reminder(self, filename, file_path):
        """显示弹窗提醒 (打开编辑器)"""
        self.open_file_with_editor(filename, file_path)

    def open_file_with_editor(self, filename, file_path):
        note_type = self.note_manager.get_note_type(filename)
        editor_path = ""
        if note_type == 'markdown':
            editor_path = self.config_manager.get_setting("md_editor_path")
        elif note_type == 'image':
            editor_path = self.config_manager.get_setting("img_editor_path")

        try:
            if editor_path and os.path.exists(editor_path):
                logger.info(f"使用指定编辑器 '{editor_path}' 打开 '{file_path}'")
                subprocess.Popen([editor_path, file_path])
            else:
                logger.warning(f"编辑器路径未设置或无效，尝试使用系统默认程序打开 '{file_path}'")
                os.startfile(file_path)
        except Exception as e:
            logger.error(f"打开文件 '{file_path}' 失败: {e}")