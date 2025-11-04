#!/user/bin-env python3
# -*- coding: utf-8 -*-
import os
import sys
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk
from loguru import logger

from task_analyzer import TaskAnalyzer
from ui.left_panel import LeftPanel
from ui.settings_panel import SettingsPanel
from ui.schedule_panel import SchedulePanel
from ui.tray_icon import TrayIconManager


class App(ctk.CTk):
    # 定义颜色常量
    DEFAULT_BG_COLOR = "#2b2b2b"
    SCHEDULED_BG_COLOR = "#264C2D"  # 一个比较柔和的深绿色

    def __init__(self, config_manager, note_manager, scheduler_service):
        super().__init__()

        self.config_manager = config_manager
        self.note_manager = note_manager
        self.scheduler_service = scheduler_service
        self.selected_note = None
        self.task_analyzer = TaskAnalyzer(self.config_manager)

        self._save_geometry_after_id = None

        # --- 窗口配置 ---
        self.title("Echonote")
        window_size = self.config_manager.get_setting("window_size", [900, 700])
        window_pos = self.config_manager.get_setting("window_position", [100, 100])
        self.geometry(
            f"{window_size[0]}x{window_size[1]}+{window_pos[0]}+{window_pos[1]}"
        )

        # --- 系统托盘管理器 ---
        self.tray_manager = TrayIconManager(self)
        self.protocol("WM_DELETE_WINDOW", self.hide_window)
        self.bind("<Configure>", self.on_window_configure)

        # --- 主框架布局 ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- 可拖动的窗格 ---
        self.paned_window = tk.PanedWindow(
            self,
            orient=tk.HORIZONTAL,
            sashrelief=tk.RAISED,
            bg="#2b2b2b",
            sashwidth=5,
            opaqueresize=False,
        )
        self.paned_window.grid(row=0, column=0, sticky="nsew")

        # --- 创建并添加左侧面板 ---
        self.left_frame = LeftPanel(master=self.paned_window, app=self)
        pane_width = self.config_manager.get_setting("pane_width", 250)
        self.paned_window.add(self.left_frame, width=pane_width, minsize=150)

        # --- 创建右侧主内容框架 ---
        self.right_frame = ctk.CTkFrame(self.paned_window)
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure(1, weight=1)

        # --- 创建并添加设置面板 ---
        self.settings_frame = SettingsPanel(master=self.right_frame, app=self)
        self.settings_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))

        # --- 创建并添加调度面板 ---
        self.schedule_frame = SchedulePanel(master=self.right_frame, app=self)
        self.schedule_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(10, 20))

        # 将右侧框架添加到 PanedWindow
        self.paned_window.add(self.right_frame, minsize=400)

        # --- 初始化 ---
        self.settings_frame.load_settings_to_gui()
        self.refresh_notes_list()
        self.schedule_frame.hide_schedule_widgets()  # 默认隐藏

    def refresh_notes_list(self):
        self.note_manager.data_folder = self.settings_frame.entry_data_folder.get()
        notes = self.note_manager.scan_notes()
        self.left_frame.notes_listbox.delete(0, tk.END)
        for note in notes:
            self.left_frame.notes_listbox.insert(tk.END, note)

        self._update_listbox_colors()

        self.schedule_frame.hide_schedule_widgets()
        self.schedule_frame.label_schedule_title.configure(
            text="提醒设置 (请先在左侧选择一个笔记)"
        )
        self.selected_note = None

    def _update_listbox_colors(self):
        """遍历列表中的所有项目，并根据是否存在调度来设置背景色"""
        all_notes = self.left_frame.notes_listbox.get(0, tk.END)
        for i, note_name in enumerate(all_notes):
            if self.config_manager.get_note_schedule(note_name):
                self.left_frame.notes_listbox.itemconfig(i, bg=self.SCHEDULED_BG_COLOR)
            else:
                self.left_frame.notes_listbox.itemconfig(i, bg=self.DEFAULT_BG_COLOR)

    def on_note_select(self, event=None):
        selection_indices = self.left_frame.notes_listbox.curselection()
        if not selection_indices:
            return

        selected_index = selection_indices[0]
        self.selected_note = self.left_frame.notes_listbox.get(selected_index)

        self.schedule_frame.label_schedule_title.configure(
            text=f"设置: {self.selected_note}"
        )
        self.schedule_frame.show_schedule_widgets()

        schedule_info = self.config_manager.get_note_schedule(self.selected_note)
        self.schedule_frame.parse_and_load_schedule_rule(schedule_info)

    def open_note_with_editor(self):
        """使用配置的编辑器打开当前选中的笔记"""
        if not self.selected_note:
            messagebox.showwarning("警告", "请先从左侧选择一个笔记。")
            return

        data_folder = self.config_manager.get_setting("data_folder")
        if not data_folder:
            logger.error("无法打开文件，因为数据文件夹未设置。")
            messagebox.showerror("错误", "数据文件夹未设置。")
            return

        file_path = os.path.join(data_folder, self.selected_note)
        if not os.path.exists(file_path):
            logger.error(f"无法打开文件，文件不存在: {file_path}")
            messagebox.showerror("错误", f"文件不存在: {self.selected_note}")
            return

        self.scheduler_service.open_file_with_editor(self.selected_note, file_path)

    def _save_geometry(self):
        """内部方法，用于保存窗口几何信息"""
        if self.winfo_width() > 50 and self.winfo_height() > 50:
            logger.info("保存窗口位置和大小...")
            self.config_manager.set_geometry_settings(
                size=[self.winfo_width(), self.winfo_height()],
                position=[self.winfo_x(), self.winfo_y()],
                pane_width=self.left_frame.winfo_width(),
            )

    def on_window_configure(self, event=None):
        """由<Configure>事件绑定的回调函数，使用延迟保存以避免过于频繁的写入"""
        if event and event.widget == self:
            if self._save_geometry_after_id:
                self.after_cancel(self._save_geometry_after_id)

            self._save_geometry_after_id = self.after(500, self._save_geometry)

    def hide_window(self):
        """隐藏窗口到系统托盘"""
        if self._save_geometry_after_id:
            self.after_cancel(self._save_geometry_after_id)
            self._save_geometry_after_id = None

        self._save_geometry()
        self.withdraw()
        self.tray_manager.setup_tray_icon()

    def quit_app_from_tray(self, icon, item):
        """完全退出应用程序"""
        logger.info("正在退出应用程序...")
        if self._save_geometry_after_id:
            self.after_cancel(self._save_geometry_after_id)
            self._save_geometry_after_id = None

        self._save_geometry()
        icon.stop()
        self.scheduler_service.stop()
        self.quit()
        sys.exit()