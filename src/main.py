#!/user/bin/env python3
# -*- coding: utf-8 -*-
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import sys
from loguru import logger
from PIL import Image
import pystray
import threading

# 导入我们自己的模块
from config_manager import ConfigManager
from note_manager import NoteManager
from scheduler_service import SchedulerService
import startup

# --- 全局配置 ---
ctk.set_appearance_mode("System")  # Modes: "System" (default), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (default), "green", "dark-blue"

# --- 日志配置 ---
log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs', 'app.log')
logger.add(log_path, rotation="10 MB", retention="7 days", encoding="utf-8", level="INFO")


class App(ctk.CTk):
    def __init__(self, config_manager, note_manager, scheduler_service):
        super().__init__()

        self.config_manager = config_manager
        self.note_manager = note_manager
        self.scheduler_service = scheduler_service
        self.tray_icon = None

        # --- 窗口配置 ---
        self.title("定期信息提示系统")
        window_size = self.config_manager.get_setting("window_size", [900, 700])
        self.geometry(f"{window_size[0]}x{window_size[1]}")
        self.protocol("WM_DELETE_WINDOW", self.hide_window)  # 关闭窗口时隐藏而非退出
        self.bind("<Configure>", self.on_window_resize)  # 绑定窗口大小改变事件

        # --- 主框架布局 ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- 左侧笔记列表框架 ---
        self.left_frame = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.left_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.left_frame.grid_rowconfigure(1, weight=1)

        self.label_notes = ctk.CTkLabel(self.left_frame, text="笔记列表", font=ctk.CTkFont(size=16, weight="bold"))
        self.label_notes.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.notes_listbox = tk.Listbox(self.left_frame, bg="#2b2b2b", fg="white", selectbackground="#1f6aa5",
                                        borderwidth=0, highlightthickness=0, font=("Segoe UI", 12))
        self.notes_listbox.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)
        self.notes_listbox.bind("<<ListboxSelect>>", self.on_note_select)

        self.refresh_button = ctk.CTkButton(self.left_frame, text="刷新笔记", command=self.refresh_notes_list)
        self.refresh_button.grid(row=2, column=0, padx=20, pady=10)

        # --- 右侧主内容框架 ---
        self.right_frame = ctk.CTkFrame(self)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.right_frame.grid_columnconfigure(1, weight=1)

        # --- 设置区域 ---
        self.settings_frame = ctk.CTkFrame(self.right_frame)
        self.settings_frame.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 20))
        self.settings_frame.grid_columnconfigure(1, weight=1)

        # 数据文件夹
        self.label_data_folder = ctk.CTkLabel(self.settings_frame, text="数据文件夹:")
        self.label_data_folder.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.entry_data_folder = ctk.CTkEntry(self.settings_frame, placeholder_text="点击右侧按钮选择笔记存放的文件夹")
        self.entry_data_folder.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.entry_data_folder.bind("<FocusOut>", self.on_path_entry_focus_out)
        self.btn_browse_data = ctk.CTkButton(self.settings_frame, text="浏览", width=80,
                                             command=self.browse_data_folder)
        self.btn_browse_data.grid(row=0, column=2, padx=10, pady=10)

        # MD编辑器
        self.label_md_editor = ctk.CTkLabel(self.settings_frame, text="MD编辑器:")
        self.label_md_editor.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.entry_md_editor = ctk.CTkEntry(self.settings_frame, placeholder_text="选择你的Markdown编辑器 (.exe)")
        self.entry_md_editor.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        self.entry_md_editor.bind("<FocusOut>", self.on_path_entry_focus_out)
        self.btn_browse_md = ctk.CTkButton(self.settings_frame, text="浏览", width=80, command=self.browse_md_editor)
        self.btn_browse_md.grid(row=1, column=2, padx=10, pady=10)

        # 图片编辑器
        self.label_img_editor = ctk.CTkLabel(self.settings_frame, text="图片查看器:")
        self.label_img_editor.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.entry_img_editor = ctk.CTkEntry(self.settings_frame, placeholder_text="选择你的图片查看器 (.exe)")
        self.entry_img_editor.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        self.entry_img_editor.bind("<FocusOut>", self.on_path_entry_focus_out)
        self.btn_browse_img = ctk.CTkButton(self.settings_frame, text="浏览", width=80, command=self.browse_img_editor)
        self.btn_browse_img.grid(row=2, column=2, padx=10, pady=10)

        # 开机自启
        self.autostart_var = ctk.BooleanVar(value=startup.is_autostart_enabled())
        self.check_autostart = ctk.CTkCheckBox(self.settings_frame, text="开机自启", variable=self.autostart_var,
                                               command=self.toggle_autostart)
        self.check_autostart.grid(row=3, column=0, columnspan=3, padx=10, pady=10, sticky="w")

        # --- 调度配置区域 ---
        self.schedule_frame = ctk.CTkFrame(self.right_frame)
        self.schedule_frame.grid(row=1, column=0, columnspan=3, sticky="nsew")
        self.schedule_frame.grid_columnconfigure(1, weight=1)
        self.schedule_frame.grid_rowconfigure(1, weight=1)

        self.label_schedule_title = ctk.CTkLabel(self.schedule_frame, text="提醒设置 (请先在左侧选择一个笔记)",
                                                 font=ctk.CTkFont(size=14))
        self.label_schedule_title.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

        # 提醒模式
        self.label_mode = ctk.CTkLabel(self.schedule_frame, text="提醒模式:")
        self.mode_var = ctk.StringVar(value="light")
        self.radio_light = ctk.CTkRadioButton(self.schedule_frame, text="轻度提醒 (系统通知)", variable=self.mode_var,
                                              value="light")
        self.radio_popup = ctk.CTkRadioButton(self.schedule_frame, text="弹窗提醒 (打开文件)", variable=self.mode_var,
                                              value="popup")

        # 调度规则输入
        self.label_rule = ctk.CTkLabel(self.schedule_frame, text="调度规则:")
        self.entry_rule = ctk.CTkEntry(self.schedule_frame,
                                       placeholder_text="例如: every().day.at('10:30') 或 every(5).minutes")

        # 保存按钮
        self.btn_save_schedule = ctk.CTkButton(self.schedule_frame, text="保存此笔记的设置",
                                               command=self.save_current_schedule)
        self.btn_clear_schedule = ctk.CTkButton(self.schedule_frame, text="清除此笔记的设置",
                                                command=self.clear_current_schedule, fg_color="transparent",
                                                border_width=2)

        # --- 初始化 ---
        self.load_settings_to_gui()
        self.refresh_notes_list()
        self.hide_schedule_widgets()  # 默认隐藏

    def hide_schedule_widgets(self):
        self.label_mode.grid_forget()
        self.radio_light.grid_forget()
        self.radio_popup.grid_forget()
        self.label_rule.grid_forget()
        self.entry_rule.grid_forget()
        self.btn_save_schedule.grid_forget()
        self.btn_clear_schedule.grid_forget()

    def show_schedule_widgets(self):
        self.label_mode.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.radio_light.grid(row=2, column=0, padx=20, pady=5, sticky="w")
        self.radio_popup.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        self.label_rule.grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.entry_rule.grid(row=4, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        self.btn_save_schedule.grid(row=5, column=0, padx=10, pady=20, sticky="w")
        self.btn_clear_schedule.grid(row=5, column=1, padx=10, pady=20, sticky="w")

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
        self.hide_schedule_widgets()
        self.label_schedule_title.configure(text="提醒设置 (请先在左侧选择一个笔记)")

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
        if schedule_info:
            self.mode_var.set(schedule_info.get("mode", "light"))
            self.entry_rule.delete(0, tk.END)
            self.entry_rule.insert(0, schedule_info.get("schedule", ""))
        else:
            # 清空旧的显示
            self.mode_var.set("light")
            self.entry_rule.delete(0, tk.END)

    def on_path_entry_focus_out(self, event=None):
        """当路径输入框失去焦点时触发保存，并根据情况刷新笔记列表。"""
        # 检查当前数据文件夹路径与输入框中的路径是否不同
        current_data_folder = self.config_manager.get_setting("data_folder", "")
        new_data_folder = self.entry_data_folder.get()

        # 无论如何都保存所有三个路径设置
        self.save_gui_settings()

        # 仅当数据文件夹路径实际发生改变时才刷新笔记列表
        if event.widget == self.entry_data_folder and current_data_folder != new_data_folder:
            logger.info("数据文件夹路径已更改，刷新笔记列表。")
            self.refresh_notes_list()

    def save_current_schedule(self):
        if not hasattr(self, 'selected_note'):
            messagebox.showwarning("警告", "请先从左侧选择一个笔记。")
            return

        rule = self.entry_rule.get().strip()
        if not rule:
            messagebox.showwarning("警告", "调度规则不能为空。")
            return

        schedule_info = {
            "mode": self.mode_var.get(),
            "schedule": rule
        }
        self.config_manager.set_note_schedule(self.selected_note, schedule_info)
        messagebox.showinfo("成功", f"已保存 '{self.selected_note}' 的提醒设置。")
        self.scheduler_service.reload_schedules()

    def clear_current_schedule(self):
        if not hasattr(self, 'selected_note'):
            messagebox.showwarning("警告", "请先从左侧选择一个笔记。")
            return

        if messagebox.askyesno("确认", f"确定要清除 '{self.selected_note}' 的所有提醒设置吗？"):
            self.config_manager.set_note_schedule(self.selected_note, None)  # 传入None来删除
            self.on_note_select()  # 刷新显示
            messagebox.showinfo("成功", "已清除设置。")
            self.scheduler_service.reload_schedules()

    def toggle_autostart(self):
        enable = self.autostart_var.get()
        startup.set_autostart(enable)
        self.config_manager.set_setting("autostart", enable)

    def on_window_resize(self, event=None):
        # 我们只在主窗口上响应事件
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
        # 尝试找到一个图标文件，如果没有就使用默认的
        try:
            # 在打包后，资源文件可能在 sys._MEIPASS
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            icon_path = os.path.join(base_path, 'icon.png')  # 假设你有一个icon.png
            image = Image.open(icon_path)
        except FileNotFoundError:
            logger.warning("icon.png not found, using a default image.")
            image = Image.new('RGB', (64, 64), 'blue')

        menu = (pystray.MenuItem('显示窗口', self.show_window, default=True),
                pystray.MenuItem('退出', self.quit_app))

        self.tray_icon = pystray.Icon("name", image, "定期信息提示系统", menu)

        # 在一个独立的线程中运行托盘图标，以防阻塞主GUI线程
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