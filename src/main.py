#!/user/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
import pystray
from PIL import Image
from loguru import logger

import startup
# 导入我们自己的模块
from config_manager import ConfigManager
from note_manager import NoteManager
from scheduler_service import SchedulerService

# --- 全局配置 ---
ctk.set_appearance_mode("System")  # Modes: "System" (default), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (default), "green", "dark-blue"

# --- 日志配置 ---
log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs', 'app.log')
# 如果日志目录不存在，则创建它
os.makedirs(os.path.dirname(log_path), exist_ok=True)
logger.add(log_path, rotation="10 MB", retention="7 days", encoding="utf-8", level="INFO")


class App(ctk.CTk):
    # --- 新增：定义颜色常量 ---
    DEFAULT_BG_COLOR = "#2b2b2b"
    SCHEDULED_BG_COLOR = "#264C2D"  # 一个比较柔和的深绿色

    def __init__(self, config_manager, note_manager, scheduler_service):
        super().__init__()

        self.config_manager = config_manager
        self.note_manager = note_manager
        self.scheduler_service = scheduler_service
        self.tray_icon = None

        # --- 窗口配置 ---
        self.title("TFInformer")
        window_size = self.config_manager.get_setting("window_size", [900, 700])
        self.geometry(f"{window_size[0]}x{window_size[1]}")
        self.protocol("WM_DELETE_WINDOW", self.hide_window)  # 关闭窗口时隐藏而非退出
        self.bind("<Configure>", self.on_window_resize)  # 绑定窗口大小改变事件

        # --- 主框架布局 (修改为单列以容纳PanedWindow) ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- 新增：创建可拖动的窗格 ---
        # 使用 tk.PanedWindow 作为容器，并设置样式以匹配主题
        self.paned_window = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, bg="#2b2b2b", sashwidth=5,
                                           opaqueresize=False)
        self.paned_window.grid(row=0, column=0, sticky="nsew")

        # --- 左侧笔记列表框架 (父容器改为 paned_window) ---
        self.left_frame = ctk.CTkFrame(self.paned_window, corner_radius=0)
        self.left_frame.grid_rowconfigure(1, weight=1)
        self.left_frame.grid_columnconfigure(0, weight=1)  # 确保内部组件可以缩放

        self.label_notes = ctk.CTkLabel(self.left_frame, text="笔记列表", font=ctk.CTkFont(size=16, weight="bold"))
        self.label_notes.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.notes_listbox = tk.Listbox(self.left_frame, bg=self.DEFAULT_BG_COLOR, fg="white",
                                        selectbackground="#1f6aa5",
                                        borderwidth=0, highlightthickness=0, font=("Segoe UI", 12))
        self.notes_listbox.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)
        self.notes_listbox.bind("<<ListboxSelect>>", self.on_note_select)

        self.refresh_button = ctk.CTkButton(self.left_frame, text="刷新笔记", command=self.refresh_notes_list)
        self.refresh_button.grid(row=2, column=0, padx=20, pady=10)

        # 将左侧框架添加到 PanedWindow，并设置初始宽度和最小宽度
        self.paned_window.add(self.left_frame, width=250, minsize=150)

        # --- 右侧主内容框架 (父容器改为 paned_window) ---
        self.right_frame = ctk.CTkFrame(self.paned_window)
        self.right_frame.grid_columnconfigure(0, weight=1)  # 为内部网格配置权重
        self.right_frame.grid_rowconfigure(1, weight=1)  # 允许调度框架扩展

        # --- 设置区域 ---
        self.settings_frame = ctk.CTkFrame(self.right_frame)
        self.settings_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        self.settings_frame.grid_columnconfigure(1, weight=1)

        # 数据文件夹
        self.label_data_folder = ctk.CTkLabel(self.settings_frame, text="数据文件夹:")
        self.label_data_folder.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.entry_data_folder = ctk.CTkEntry(self.settings_frame, placeholder_text="点击右侧按钮选择笔记存放的文件夹")
        self.entry_data_folder.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.entry_data_folder.bind("<FocusOut>", self.on_path_entry_focus_out)
        self.btn_browse_data = ctk.CTkButton(self.settings_frame, text="浏览", width=80,
                                             command=self.browse_data_folder)
        self.btn_browse_data.grid(row=0, column=2, padx=(10, 5), pady=10)
        self.btn_open_data_folder = ctk.CTkButton(self.settings_frame, text="打开", width=80,
                                                  command=self.open_data_folder)
        self.btn_open_data_folder.grid(row=0, column=3, padx=(5, 10), pady=10)

        # MD编辑器
        self.label_md_editor = ctk.CTkLabel(self.settings_frame, text="MD编辑器:")
        self.label_md_editor.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.entry_md_editor = ctk.CTkEntry(self.settings_frame, placeholder_text="选择你的Markdown编辑器 (.exe)")
        self.entry_md_editor.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        self.entry_md_editor.bind("<FocusOut>", self.on_path_entry_focus_out)
        self.btn_browse_md = ctk.CTkButton(self.settings_frame, text="浏览", width=80, command=self.browse_md_editor)
        self.btn_browse_md.grid(row=1, column=2, padx=(10, 5), pady=10)
        self.btn_open_md_folder = ctk.CTkButton(self.settings_frame, text="打开", width=80,
                                                command=self.open_md_editor_folder)
        self.btn_open_md_folder.grid(row=1, column=3, padx=(5, 10), pady=10)

        # 图片编辑器
        self.label_img_editor = ctk.CTkLabel(self.settings_frame, text="图片查看器:")
        self.label_img_editor.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.entry_img_editor = ctk.CTkEntry(self.settings_frame, placeholder_text="选择你的图片查看器 (.exe)")
        self.entry_img_editor.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        self.entry_img_editor.bind("<FocusOut>", self.on_path_entry_focus_out)
        self.btn_browse_img = ctk.CTkButton(self.settings_frame, text="浏览", width=80, command=self.browse_img_editor)
        self.btn_browse_img.grid(row=2, column=2, padx=(10, 5), pady=10)
        self.btn_open_img_folder = ctk.CTkButton(self.settings_frame, text="打开", width=80,
                                                 command=self.open_img_editor_folder)
        self.btn_open_img_folder.grid(row=2, column=3, padx=(5, 10), pady=10)

        # 开机自启
        self.autostart_var = ctk.BooleanVar(value=startup.is_autostart_enabled())
        self.check_autostart = ctk.CTkCheckBox(self.settings_frame, text="开机自启", variable=self.autostart_var,
                                               command=self.toggle_autostart)
        self.check_autostart.grid(row=3, column=0, columnspan=3, padx=10, pady=10, sticky="w")

        # --- 调度配置区域 ---
        self.schedule_frame = ctk.CTkFrame(self.right_frame)
        self.schedule_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(10, 20))
        self.schedule_frame.grid_columnconfigure(0, weight=1)  # 让内部组件可以扩展

        self.label_schedule_title = ctk.CTkLabel(self.schedule_frame, text="提醒设置 (请先在左侧选择一个笔记)",
                                                 font=ctk.CTkFont(size=14))
        self.label_schedule_title.grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky="w")

        # --- 初始化调度规则GUI构建器 ---
        self.init_schedule_builder()

        # 将右侧框架添加到 PanedWindow，并设置最小宽度
        self.paned_window.add(self.right_frame, minsize=400)

        # --- 初始化 ---
        self.load_settings_to_gui()
        self.refresh_notes_list()
        self.hide_schedule_widgets()  # 默认隐藏

    def init_schedule_builder(self):
        """创建用于构建调度规则的GUI组件"""
        # --- 提醒模式 ---
        self.label_mode = ctk.CTkLabel(self.schedule_frame, text="提醒模式:")
        self.mode_var = ctk.StringVar(value="light")
        self.radio_light = ctk.CTkRadioButton(self.schedule_frame, text="轻度提醒 (系统通知)", variable=self.mode_var,
                                              value="light")
        self.radio_popup = ctk.CTkRadioButton(self.schedule_frame, text="弹窗提醒 (打开文件)", variable=self.mode_var,
                                              value="popup")

        # --- 调度规则构建器 ---
        self.label_rule_header = ctk.CTkLabel(self.schedule_frame, text="提醒规则:")

        # 规则构建器主框架
        self.rule_builder_frame = ctk.CTkFrame(self.schedule_frame, fg_color="transparent")

        # 频率设置
        self.label_every = ctk.CTkLabel(self.rule_builder_frame, text="每")
        self.interval_var = ctk.StringVar(value="1")
        self.entry_interval = ctk.CTkEntry(self.rule_builder_frame, textvariable=self.interval_var, width=50)

        self.unit_map = {"分钟": "minutes", "小时": "hours", "天": "days", "周": "weeks"}
        self.unit_map_rev = {v: k for k, v in self.unit_map.items()}
        self.unit_var = ctk.StringVar(value="天")
        self.option_unit = ctk.CTkOptionMenu(self.rule_builder_frame, variable=self.unit_var,
                                             values=list(self.unit_map.keys()), command=self.on_unit_change)

        # 星期选择
        self.weekday_frame = ctk.CTkFrame(self.schedule_frame, fg_color="transparent")
        self.label_weekday = ctk.CTkLabel(self.weekday_frame, text="在:")
        self.weekday_map = {"周一": "monday", "周二": "tuesday", "周三": "wednesday", "周四": "thursday",
                            "周五": "friday", "周六": "saturday", "周日": "sunday"}
        self.weekday_map_rev = {v: k for k, v in self.weekday_map.items()}
        self.weekday_var = ctk.StringVar()
        self.weekday_selector = ctk.CTkSegmentedButton(self.weekday_frame, values=list(self.weekday_map.keys()),
                                                       variable=self.weekday_var)

        # 时间选择
        self.time_frame = ctk.CTkFrame(self.schedule_frame, fg_color="transparent")
        self.label_at = ctk.CTkLabel(self.time_frame, text="在:")
        self.hour_var = ctk.StringVar(value="10")
        self.minute_var = ctk.StringVar(value="30")
        self.option_hour = ctk.CTkOptionMenu(self.time_frame, variable=self.hour_var,
                                             values=[f"{h:02d}" for h in range(24)])
        self.label_time_sep = ctk.CTkLabel(self.time_frame, text=":")
        self.option_minute = ctk.CTkOptionMenu(self.time_frame, variable=self.minute_var,
                                               values=[f"{m:02d}" for m in range(0,60,5)])

        # 保存与清除按钮
        self.btn_save_schedule = ctk.CTkButton(self.schedule_frame, text="保存此笔记的设置",
                                               command=self.save_current_schedule)
        self.btn_clear_schedule = ctk.CTkButton(self.schedule_frame, text="清除此笔记的设置",
                                                command=self.clear_current_schedule,
                                                fg_color="transparent", border_width=2)

        # --- 布局规则构建器 ---
        self.label_every.grid(row=0, column=0, padx=(0, 5), pady=5)
        self.entry_interval.grid(row=0, column=1, padx=5, pady=5)
        self.option_unit.grid(row=0, column=2, padx=5, pady=5)

        self.label_weekday.grid(row=0, column=0, padx=(0, 10), pady=5)
        self.weekday_selector.grid(row=0, column=1, padx=0, pady=5)

        self.label_at.grid(row=0, column=0, padx=(0, 10), pady=5)
        self.option_hour.grid(row=0, column=1, padx=0, pady=5)
        self.label_time_sep.grid(row=0, column=2, padx=5, pady=5)
        self.option_minute.grid(row=0, column=3, padx=0, pady=5)

    def reset_schedule_gui(self):
        """将调度GUI重置为默认状态"""
        self.mode_var.set("light")
        self.interval_var.set("1")
        self.unit_var.set("天")
        self.weekday_var.set("")  # 清除星期选择
        self.hour_var.set("10")
        self.minute_var.set("30")
        self.on_unit_change()  # 更新UI可见性

    def hide_schedule_widgets(self):
        self.label_mode.grid_forget()
        self.radio_light.grid_forget()
        self.radio_popup.grid_forget()
        self.label_rule_header.grid_forget()
        self.rule_builder_frame.grid_forget()
        self.weekday_frame.grid_forget()
        self.time_frame.grid_forget()
        self.btn_save_schedule.grid_forget()
        self.btn_clear_schedule.grid_forget()

    def show_schedule_widgets(self):
        self.label_mode.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        self.radio_light.grid(row=2, column=0, columnspan=2, padx=20, pady=5, sticky="w")
        self.radio_popup.grid(row=2, column=2, columnspan=2, padx=10, pady=5, sticky="w")

        self.label_rule_header.grid(row=3, column=0, columnspan=2, padx=10, pady=(10, 0), sticky="w")
        self.rule_builder_frame.grid(row=4, column=0, columnspan=4, padx=10, pady=0, sticky="w")

        # 动态显示的组件由 on_unit_change 控制
        self.on_unit_change()

        self.btn_save_schedule.grid(row=7, column=0, columnspan=2, padx=10, pady=20, sticky="w")
        self.btn_clear_schedule.grid(row=7, column=2, columnspan=2, padx=10, pady=20, sticky="w")

    def on_unit_change(self, selected_unit=None):
        """根据选择的单位（分钟/小时/天/周）更新UI"""
        if selected_unit is None:
            selected_unit = self.unit_var.get()

        if selected_unit == "周":
            self.weekday_frame.grid(row=5, column=0, columnspan=4, padx=10, pady=5, sticky="w")
            self.time_frame.grid(row=6, column=0, columnspan=4, padx=10, pady=5, sticky="w")
        elif selected_unit == "天":
            self.weekday_frame.grid_forget()
            self.time_frame.grid(row=6, column=0, columnspan=4, padx=10, pady=5, sticky="w")
        else:  # 分钟 或 小时
            self.weekday_frame.grid_forget()
            self.time_frame.grid_forget()

    def browse_folder(self, entry_widget):
        folder = filedialog.askdirectory()
        if folder:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, folder)
            self.save_gui_settings()  # 保存并刷新
            self.refresh_notes_list()

    def browse_file(self, entry_widget):
        file = filedialog.askopenfilename(filetypes=[("Executable files", "*.exe")])
        if file:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, file)
            self.save_gui_settings()

    def browse_data_folder(self):
        self.browse_folder(self.entry_data_folder)

    def browse_md_editor(self):
        self.browse_file(self.entry_md_editor)

    def browse_img_editor(self):
        self.browse_file(self.entry_img_editor)

    def open_folder(self, path):
        """打开指定路径的文件夹（跨平台兼容）"""
        try:
            if os.path.exists(path):
                if sys.platform == "win32":
                    os.startfile(path)
                elif sys.platform == "darwin":  # macOS
                    os.system(f'open "{path}"')
                else:  # Linux
                    os.system(f'xdg-open "{path}"')
            else:
                messagebox.showerror("错误", f"路径不存在: {path}")
        except Exception as e:
            logger.error(f"打开文件夹失败: {e}")
            messagebox.showerror("错误", f"无法打开文件夹: {str(e)}")

    def open_data_folder(self):
        """打开数据文件夹"""
        folder_path = self.entry_data_folder.get()
        if folder_path:
            self.open_folder(folder_path)
        else:
            messagebox.showwarning("警告", "请先设置数据文件夹路径")

    def open_md_editor_folder(self):
        """打开MD编辑器所在文件夹"""
        editor_path = self.entry_md_editor.get()
        if editor_path:
            folder_path = os.path.dirname(editor_path)
            self.open_folder(folder_path)
        else:
            messagebox.showwarning("警告", "请先设置MD编辑器路径")

    def open_img_editor_folder(self):
        """打开图片编辑器所在文件夹"""
        editor_path = self.entry_img_editor.get()
        if editor_path:
            folder_path = os.path.dirname(editor_path)
            self.open_folder(folder_path)
        else:
            messagebox.showwarning("警告", "请先设置图片查看器路径")

    def load_settings_to_gui(self):
        self.entry_data_folder.insert(0, self.config_manager.get_setting("data_folder", ""))
        self.entry_md_editor.insert(0, self.config_manager.get_setting("md_editor_path", ""))
        self.entry_img_editor.insert(0, self.config_manager.get_setting("img_editor_path", ""))

    def save_gui_settings(self):
        self.config_manager.set_setting("data_folder", self.entry_data_folder.get())
        self.config_manager.set_setting("md_editor_path", self.entry_md_editor.get())
        self.config_manager.set_setting("img_editor_path", self.entry_img_editor.get())
        logger.info("全局设置已更新。")

    def refresh_notes_list(self):
        self.note_manager.data_folder = self.entry_data_folder.get()
        notes = self.note_manager.scan_notes()
        self.notes_listbox.delete(0, tk.END)
        for note in notes:
            self.notes_listbox.insert(tk.END, note)

        # --- 修改：刷新后更新颜色 ---
        self._update_listbox_colors()

        self.hide_schedule_widgets()
        self.label_schedule_title.configure(text="提醒设置 (请先在左侧选择一个笔记)")

    # --- 新增：更新列表颜色的辅助函数 ---
    def _update_listbox_colors(self):
        """遍历列表中的所有项目，并根据是否存在调度来设置背景色"""
        all_notes = self.notes_listbox.get(0, tk.END)
        for i, note_name in enumerate(all_notes):
            if self.config_manager.get_note_schedule(note_name):
                self.notes_listbox.itemconfig(i, bg=self.SCHEDULED_BG_COLOR)
            else:
                self.notes_listbox.itemconfig(i, bg=self.DEFAULT_BG_COLOR)

    def on_note_select(self, event=None):
        selection_indices = self.notes_listbox.curselection()
        if not selection_indices:
            return

        selected_index = selection_indices[0]
        self.selected_note = self.notes_listbox.get(selected_index)

        self.label_schedule_title.configure(text=f"设置: {self.selected_note}")
        self.show_schedule_widgets()

        # 加载该笔记已有的配置
        schedule_info = self.config_manager.get_note_schedule(self.selected_note)
        self.parse_and_load_schedule_rule(schedule_info)

    def parse_and_load_schedule_rule(self, schedule_info):
        """解析存储的规则字符串并更新GUI"""
        if not schedule_info or "schedule" not in schedule_info:
            self.reset_schedule_gui()
            return

        self.mode_var.set(schedule_info.get("mode", "light"))
        rule = schedule_info.get("schedule", "")

        # 解析 interval: every(5) -> 5, every() -> 1
        interval_match = re.search(r"every\((\d*)\)", rule)
        self.interval_var.set(interval_match.group(1) if interval_match and interval_match.group(1) else "1")

        # 解析 unit: .minutes, .hours, .days, .weeks
        unit_match = re.search(r"\.(" + "|".join(self.unit_map.values()) + r")", rule)
        if unit_match and unit_match.group(1) in self.unit_map_rev:
            self.unit_var.set(self.unit_map_rev[unit_match.group(1)])
        else:
            self.unit_var.set("天")  # 默认

        # 解析 weekday: .monday, .tuesday ...
        weekday_match = re.search(r"\.(" + "|".join(self.weekday_map.values()) + r")", rule)
        if weekday_match and weekday_match.group(1) in self.weekday_map_rev:
            self.weekday_var.set(self.weekday_map_rev[weekday_match.group(1)])
        else:
            self.weekday_var.set("")  # 清空

        # 解析 time: .at("10:30")
        time_match = re.search(r"at\(['\"](\d{1,2}:\d{2})['\"]\)", rule)
        if time_match:
            hour, minute = time_match.group(1).split(":")
            self.hour_var.set(f"{int(hour):02d}")
            self.minute_var.set(f"{int(minute):02d}")
        else:
            self.hour_var.set("10")
            self.minute_var.set("30")

        self.on_unit_change()  # 根据解析结果更新UI

    def on_path_entry_focus_out(self, event=None):
        """当路径输入框失去焦点时触发保存，并根据情况刷新笔记列表。"""
        current_data_folder = self.config_manager.get_setting("data_folder", "")
        new_data_folder = self.entry_data_folder.get()
        self.save_gui_settings()
        if event and event.widget == self.entry_data_folder and current_data_folder != new_data_folder:
            logger.info("数据文件夹路径已更改，刷新笔记列表。")
            self.refresh_notes_list()

    def save_current_schedule(self):
        if not hasattr(self, 'selected_note'):
            messagebox.showwarning("警告", "请先从左侧选择一个笔记。")
            return

        # 从GUI组件构建规则字符串
        try:
            interval = int(self.interval_var.get())
            if interval <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("警告", "频率间隔必须是一个正整数。")
            return

        unit_key = self.unit_var.get()
        unit_val = self.unit_map[unit_key]

        rule_parts = []
        # every(5) or every()
        rule_parts.append(f"every({interval if interval > 1 else ''})")

        # .monday, .tuesday etc.
        if unit_key == "周":
            weekday_key = self.weekday_var.get()
            if not weekday_key:
                messagebox.showwarning("警告", "选择“周”为单位时，必须选择具体是周几。")
                return
            rule_parts.append(f".{self.weekday_map[weekday_key]}")

        # .minutes, .hours, .day (singular for day)
        # The schedule library is flexible with singular/plural, but we'll be consistent.
        if unit_key != "周":
            rule_parts.append(f".{unit_val[:-1] if unit_val.endswith('s') else unit_val}")  # e.g., minutes -> minute

        # .at("HH:MM")
        if unit_key in ["天", "周"]:
            hour = self.hour_var.get()
            minute = self.minute_var.get()
            rule_parts.append(f".at('{hour}:{minute}')")

        final_rule = "".join(rule_parts)

        schedule_info = {
            "mode": self.mode_var.get(),
            "schedule": final_rule
        }
        self.config_manager.set_note_schedule(self.selected_note, schedule_info)
        messagebox.showinfo("成功", f"已保存 '{self.selected_note}' 的提醒设置。")

        # --- 修改：保存后更新颜色 ---
        self._update_listbox_colors()
        self.scheduler_service.reload_schedules()

    def clear_current_schedule(self):
        if not hasattr(self, 'selected_note'):
            messagebox.showwarning("警告", "请先从左侧选择一个笔记。")
            return

        if messagebox.askyesno("确认", f"确定要清除 '{self.selected_note}' 的所有提醒设置吗？"):
            self.config_manager.set_note_schedule(self.selected_note, None)  # 传入None来删除
            self.reset_schedule_gui()
            messagebox.showinfo("成功", "已清除设置。")

            # --- 修改：清除后更新颜色 ---
            self._update_listbox_colors()
            self.scheduler_service.reload_schedules()

    def toggle_autostart(self):
        enable = self.autostart_var.get()
        startup.set_autostart(enable)
        self.config_manager.set_setting("autostart", enable)

    def on_window_resize(self, event=None):
        if event and event.widget == self:
            self.config_manager.set_setting("window_size", [self.winfo_width(), self.winfo_height()])

    def hide_window(self):
        """隐藏窗口到系统托盘"""
        self.withdraw()
        if self.tray_icon is None or not self.tray_icon.visible:
            self.setup_tray_icon()

    def show_window(self, icon, item):
        """从系统托盘恢复窗口"""
        icon.stop()
        self.tray_icon = None
        self.after(0, self.deiconify)

    def quit_app(self, icon, item):
        """完全退出应用程序"""
        logger.info("正在退出应用程序...")
        icon.stop()
        self.scheduler_service.stop()
        self.quit()
        sys.exit()

    def setup_tray_icon(self):
        """创建并运行系统托盘图标"""
        try:
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            icon_path = os.path.join(base_path, 'icon.png')
            image = Image.open(icon_path)
        except Exception:
            logger.warning(f"图标文件 'icon.png' 未找到, 将使用默认图标。")
            image = Image.new('RGB', (64, 64), 'blue')

        menu = (pystray.MenuItem('显示窗口', self.show_window, default=True),
                pystray.MenuItem('退出', self.quit_app))

        self.tray_icon = pystray.Icon("name", image, "TFInformer", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()


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