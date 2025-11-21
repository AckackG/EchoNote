#!/user/bin/env python3
# -*- coding: utf-8 -*-
#!/user/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk
from loguru import logger


class LeftPanel(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, corner_radius=0)
        self.app = app

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(self, placeholder_text="搜索笔记...", font=ctk.CTkFont(size=16))
        self.search_entry.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        self.search_entry.bind("<KeyRelease>", self.filter_notes)

        self.notes_listbox = tk.Listbox(self, bg=self.app.DEFAULT_BG_COLOR, fg="white",
                                        selectbackground="#1f6aa5",
                                        borderwidth=0, highlightthickness=0, font=("Segoe UI", 12))
        self.notes_listbox.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)
        self.notes_listbox.bind("<<ListboxSelect>>", self.app.on_note_select)

        self.all_notes = [] # Cache for all notes
        self.pypinyin_available = False
        try:
            from pypinyin import pinyin, Style
            self.pypinyin = pinyin
            self.pypinyin_style = Style
            self.pypinyin_available = True
            logger.info("pypinyin library loaded successfully.")
        except ImportError:
            logger.warning("pypinyin library not found. Pinyin search will be disabled.")
            pass

    def update_notes(self, notes: list):
        self.all_notes = sorted(notes, key=lambda s: s.lower())
        self._display_notes(self.all_notes)

    def _display_notes(self, notes: list):
        self.notes_listbox.delete(0, tk.END)
        for note in notes:
            self.notes_listbox.insert(tk.END, note)
        if notes:
            self.notes_listbox.selection_set(0)
            self.app.on_note_select()

    def filter_notes(self, event=None):
        query = self.search_entry.get().strip().lower()
        if not query:
            self._display_notes(self.all_notes)
            return

        filtered_notes = []
        for note in self.all_notes:
            if query in note.lower():
                filtered_notes.append(note)
            elif self.pypinyin_available:
                pinyin_list = self.pypinyin(note, style=self.pypinyin_style.NORMAL)
                pinyin_str = "".join([s[0] for s in pinyin_list])
                if query in pinyin_str.lower():
                    filtered_notes.append(note)
        self._display_notes(filtered_notes)

    def open_data_folder(self):
        """打开数据文件夹"""
        folder_path = self.app.settings_frame.entry_data_folder.get()
        if folder_path:
            self.open_folder(folder_path)
        else:
            messagebox.showwarning("警告", "请先设置数据文件夹路径")

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

        # --- 左侧底部按钮框架 ---
        self.left_bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.left_bottom_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.left_bottom_frame.grid_columnconfigure(0, weight=1)
        self.left_bottom_frame.grid_columnconfigure(1, weight=1)

        self.refresh_button = ctk.CTkButton(self.left_bottom_frame, text="刷新笔记", command=self.app.refresh_notes_list)
        self.refresh_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.btn_open_data_folder = ctk.CTkButton(self.left_bottom_frame, text="浏览目录",
                                                  command=self.open_data_folder)
        self.btn_open_data_folder.grid(row=0, column=1, padx=(5, 0), sticky="ew")

    def open_data_folder(self):
        """打开数据文件夹"""
        folder_path = self.app.settings_frame.entry_data_folder.get()
        if folder_path:
            self.open_folder(folder_path)
        else:
            messagebox.showwarning("警告", "请先设置数据文件夹路径")

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