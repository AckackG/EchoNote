#!/user/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk
from loguru import logger

try:
    from pypinyin import pinyin, Style
    PYPINYIN_AVAILABLE = True
except ImportError:
    PYPINYIN_AVAILABLE = False


class LeftPanel(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, corner_radius=0)
        self.app = app
        self.all_notes = []  # Cache for all notes

        if PYPINYIN_AVAILABLE:
            logger.info("pypinyin library loaded successfully.")
        else:
            logger.warning("pypinyin library not found. Pinyin search will be disabled.")

        # --- Layout Configuration ---
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # --- Top Frame for Search ---
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        self.top_frame.grid_columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(self.top_frame, placeholder_text="搜索笔记...支持拼音", font=ctk.CTkFont(size=14))
        self.search_entry.grid(row=0, column=0, sticky="ew")
        self.search_entry.bind("<KeyRelease>", self.filter_notes)

        # --- Notes Listbox ---
        self.notes_listbox = tk.Listbox(self, bg=self.app.DEFAULT_BG_COLOR, fg="white",
                                        selectbackground="#1f6aa5",
                                        borderwidth=0, highlightthickness=0, font=("Segoe UI", 12))
        self.notes_listbox.grid(row=1, column=0, sticky='nsew', padx=10, pady=5)
        self.notes_listbox.bind("<<ListboxSelect>>", self.app.on_note_select)

        # --- Bottom Frame for Buttons ---
        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_frame.grid(row=2, column=0, padx=10, pady=(5, 10), sticky="ew")
        self.bottom_frame.grid_columnconfigure((0, 1), weight=1)

        self.refresh_button = ctk.CTkButton(self.bottom_frame, text="刷新", command=self.app.refresh_notes_list)
        self.refresh_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.btn_open_folder = ctk.CTkButton(self.bottom_frame, text="打开目录", command=self.open_data_folder)
        self.btn_open_folder.grid(row=0, column=1, padx=(5, 0), sticky="ew")

    def update_notes(self, notes: list):
        self.all_notes = sorted(notes, key=lambda s: s.lower())
        self._display_notes(self.all_notes)

    def _display_notes(self, notes: list):
        self.notes_listbox.delete(0, tk.END)
        for note in notes:
            self.notes_listbox.insert(tk.END, note)

        # Update colors after list is populated
        self.app._update_listbox_colors()

        if notes:
            # Check if a selection is still valid, otherwise select the first
            current_selection = self.app.selected_note
            if current_selection and current_selection in notes:
                try:
                    idx = notes.index(current_selection)
                    self.notes_listbox.selection_set(idx)
                except ValueError:
                    self.notes_listbox.selection_set(0) # Fallback
            else:
                self.notes_listbox.selection_set(0)

        # Trigger selection event to update the right panel
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
            elif PYPINYIN_AVAILABLE:
                pinyin_list = pinyin(note, style=Style.NORMAL)
                pinyin_str = "".join([s[0] for s in pinyin_list])
                if query in pinyin_str.lower():
                    filtered_notes.append(note)

        self._display_notes(filtered_notes)

    def open_data_folder(self):
        """Opens the data folder in the system's file explorer."""
        folder_path = self.app.settings_frame.entry_data_folder.get()
        if folder_path and os.path.isdir(folder_path):
            self.open_folder(folder_path)
        else:
            messagebox.showwarning("Warning", "The data folder path is not set or does not exist.")

    @staticmethod
    def open_folder(path):
        """Opens a folder in the system's file explorer (cross-platform)."""
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":  # macOS
                os.system(f'open "{path}"')
            else:  # Linux
                os.system(f'xdg-open "{path}"')
        except Exception as e:
            logger.error(f"Failed to open folder: {e}")
            messagebox.showerror("Error", f"Could not open the folder: {str(e)}")