#!/user/bin/env python3
# -*- coding: utf-8 -*-
#!/user/bin/env python3
# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from loguru import logger
import startup


class SettingsPanel(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app

        self.grid_columnconfigure(1, weight=1)

        # 数据文件夹
        self.label_data_folder = ctk.CTkLabel(self, text="数据文件夹:")
        self.label_data_folder.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.entry_data_folder = ctk.CTkEntry(self, placeholder_text="点击右侧按钮选择笔记存放的文件夹")
        self.entry_data_folder.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.entry_data_folder.bind("<FocusOut>", self.on_path_entry_focus_out)
        self.btn_browse_data = ctk.CTkButton(self, text="设置", width=80, command=self.browse_data_folder)
        self.btn_browse_data.grid(row=0, column=2, padx=(10, 10), pady=10)

        # MD编辑器
        self.label_md_editor = ctk.CTkLabel(self, text="MD编辑器:")
        self.label_md_editor.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.entry_md_editor = ctk.CTkEntry(self, placeholder_text="选择你的Markdown编辑器 (.exe)")
        self.entry_md_editor.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        self.entry_md_editor.bind("<FocusOut>", self.on_path_entry_focus_out)
        self.btn_browse_md = ctk.CTkButton(self, text="设置", width=80, command=self.browse_md_editor)
        self.btn_browse_md.grid(row=1, column=2, padx=(10, 10), pady=10)

        # 图片编辑器
        self.label_img_editor = ctk.CTkLabel(self, text="图片查看器:")
        self.label_img_editor.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.entry_img_editor = ctk.CTkEntry(self, placeholder_text="选择你的图片查看器 (.exe)")
        self.entry_img_editor.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        self.entry_img_editor.bind("<FocusOut>", self.on_path_entry_focus_out)
        self.btn_browse_img = ctk.CTkButton(self, text="设置", width=80, command=self.browse_img_editor)
        self.btn_browse_img.grid(row=2, column=2, padx=(10, 10), pady=10)

        # 开机自启
        self.autostart_var = ctk.BooleanVar(value=startup.is_autostart_enabled())
        self.check_autostart = ctk.CTkCheckBox(self, text="开机自启", variable=self.autostart_var,
                                               command=self.toggle_autostart)
        self.check_autostart.grid(row=3, column=0, columnspan=3, padx=10, pady=10, sticky="w")

    def browse_folder(self, entry_widget):
        folder = filedialog.askdirectory()
        if folder:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, folder)
            self.save_gui_settings()
            self.app.refresh_notes_list()

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
        self.entry_data_folder.insert(0, self.app.config_manager.get_setting("data_folder", ""))
        self.entry_md_editor.insert(0, self.app.config_manager.get_setting("md_editor_path", ""))
        self.entry_img_editor.insert(0, self.app.config_manager.get_setting("img_editor_path", ""))

    def save_gui_settings(self):
        self.app.config_manager.set_setting("data_folder", self.entry_data_folder.get())
        self.app.config_manager.set_setting("md_editor_path", self.entry_md_editor.get())
        self.app.config_manager.set_setting("img_editor_path", self.entry_img_editor.get())
        logger.info("全局设置已更新。")

    def on_path_entry_focus_out(self, event=None):
        current_data_folder = self.app.config_manager.get_setting("data_folder", "")
        new_data_folder = self.entry_data_folder.get()
        self.save_gui_settings()
        if event and event.widget == self.entry_data_folder and current_data_folder != new_data_folder:
            logger.info("数据文件夹路径已更改，刷新笔记列表。")
            self.app.refresh_notes_list()

    def toggle_autostart(self):
        enable = self.autostart_var.get()
        startup.set_autostart(enable)
        self.app.config_manager.set_setting("autostart", enable)