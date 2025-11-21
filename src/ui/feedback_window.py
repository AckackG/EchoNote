#!/user/bin/env python3
# -*- coding: utf-8 -*-
import customtkinter as ctk
import tkinter as tk
from loguru import logger

class FeedbackWindow(ctk.CTkToplevel):
    def __init__(self, master, app, filename: str):
        super().__init__(master)
        self.app = app
        self.filename = filename
        self.timer_id = None

        self.overrideredirect(True)  # Remove system title bar and borders
        self.attributes("-topmost", True)  # Always on top
        self.attributes("-alpha", 0.9)  # Slight transparency

        # Initial position (bottom right, above tray icon, placeholder)
        self.initial_x = self.winfo_screenwidth() - 300  # Adjust as needed
        self.initial_y = self.winfo_screenheight() - 150 # Adjust as needed
        self.geometry(f"280x60+{self.initial_x}+{self.initial_y}")

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=0)

        self.label_filename = ctk.CTkLabel(self, text=f"回顾: {filename}",
                                           font=ctk.CTkFont(size=14, weight="bold"))
        self.label_filename.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.btn_mastered = ctk.CTkButton(self, text="✅", width=40, height=40, corner_radius=10,
                                          command=self._on_mastered, fg_color="#5D9C59", hover_color="#4a7e48")
        self.btn_mastered.grid(row=0, column=1, padx=(0, 5), pady=10, sticky="e")

        self.btn_not_mastered = ctk.CTkButton(self, text="❌", width=40, height=40, corner_radius=10,
                                             command=self._on_not_mastered, fg_color="#C62828", hover_color="#a02020")
        self.btn_not_mastered.grid(row=0, column=2, padx=(0, 10), pady=10, sticky="e")

        self._start_auto_destroy_timer()

    def _on_mastered(self):
        logger.info(f"User marked '{self.filename}' as mastered.")
        self.app.config_manager.increment_stat(self.filename, "mastered_count")
        # Optional: Adjust schedule based on mastery
        self.destroy()

    def _on_not_mastered(self):
        logger.info(f"User marked '{self.filename}' as not mastered.")
        # No explicit stat increment for 'not mastered' as 'shown_count' already covers it
        self.destroy()

    def _start_auto_destroy_timer(self):
        if self.timer_id:
            self.after_cancel(self.timer_id)
        self.timer_id = self.after(60000, self._auto_destroy) # 60 seconds

    def _auto_destroy(self):
        if self.winfo_exists():
            logger.info(f"Feedback window for '{self.filename}' auto-destroyed due to timeout.")
            self.destroy()

    def destroy(self):
        if self.timer_id:
            self.after_cancel(self.timer_id)
        super().destroy()


if __name__ == '__main__':
    # Example Usage (for testing the window independently)
    class MockApp:
        def __init__(self):
            self.config_manager = MockConfigManager()

    class MockConfigManager:
        def increment_stat(self, filename, stat_key):
            print(f"MockConfigManager: Incrementing {stat_key} for {filename}")

    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.withdraw() # Hide the main window for this test

    mock_app = MockApp()

    # Test with a dummy filename
    feedback_win = FeedbackWindow(root, mock_app, "MyTestNote.md")
    root.mainloop()
