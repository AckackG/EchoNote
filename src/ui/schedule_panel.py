#!/user/bin/env python3
# -*- coding: utf-8 -*-
#!/user/bin/env python3
# -*- coding: utf-8 -*-
import re
from tkinter import messagebox
import customtkinter as ctk


class SchedulePanel(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app

        self.grid_columnconfigure(0, weight=1)

        self.label_schedule_title = ctk.CTkLabel(self, text="提醒设置 (请先在左侧选择一个笔记)",
                                                 font=ctk.CTkFont(size=14))
        self.label_schedule_title.grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky="w")

        self._init_schedule_builder()

    def _init_schedule_builder(self):
        """创建用于构建调度规则的GUI组件"""
        # --- 提醒模式 ---
        self.label_mode = ctk.CTkLabel(self, text="提醒模式:")
        self.mode_var = ctk.StringVar(value="light")

        self.mode_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.radio_light = ctk.CTkRadioButton(self.mode_frame, text="轻度提醒 (系统通知)", variable=self.mode_var,
                                              value="light")
        self.radio_light.pack(side="left", padx=(10, 5), pady=5)
        self.radio_popup = ctk.CTkRadioButton(self.mode_frame, text="弹窗提醒", variable=self.mode_var,
                                              value="popup")
        self.radio_popup.pack(side="left", padx=5, pady=5)

        # --- 调度规则构建器 ---
        self.label_rule_header = ctk.CTkLabel(self, text="提醒规则:")
        self.rule_builder_frame = ctk.CTkFrame(self, fg_color="transparent")

        self.label_every = ctk.CTkLabel(self.rule_builder_frame, text="每")
        self.interval_var = ctk.StringVar(value="1")
        self.entry_interval = ctk.CTkEntry(self.rule_builder_frame, textvariable=self.interval_var, width=50)

        self.unit_map = {"分钟": "minutes", "小时": "hours", "天": "days", "周": "weeks"}
        self.unit_map_rev = {v: k for k, v in self.unit_map.items()}
        self.unit_var = ctk.StringVar(value="天")
        self.option_unit = ctk.CTkOptionMenu(self.rule_builder_frame, variable=self.unit_var,
                                             values=list(self.unit_map.keys()), command=self.on_unit_change)

        # 星期选择
        self.weekday_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.label_weekday = ctk.CTkLabel(self.weekday_frame, text="在:")
        self.weekday_map = {"周一": "monday", "周二": "tuesday", "周三": "wednesday", "周四": "thursday",
                            "周五": "friday", "周六": "saturday", "周日": "sunday"}
        self.weekday_map_rev = {v: k for k, v in self.weekday_map.items()}
        self.weekday_var = ctk.StringVar()
        self.weekday_selector = ctk.CTkSegmentedButton(self.weekday_frame, values=list(self.weekday_map.keys()),
                                                       variable=self.weekday_var)

        # 时间选择
        self.time_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.label_at = ctk.CTkLabel(self.time_frame, text="在:")
        self.hour_var = ctk.StringVar(value="10")
        self.minute_var = ctk.StringVar(value="30")
        self.option_hour = ctk.CTkOptionMenu(self.time_frame, variable=self.hour_var,
                                             values=[f"{h:02d}" for h in range(24)])
        self.label_time_sep = ctk.CTkLabel(self.time_frame, text=":")
        self.option_minute = ctk.CTkOptionMenu(self.time_frame, variable=self.minute_var,
                                               values=[f"{m:02d}" for m in range(0, 60, 5)])

        # --- 按钮区域 ---
        self.button_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_save_schedule = ctk.CTkButton(self.button_frame, text="保存此笔记设置",
                                               command=self.save_current_schedule, fg_color="green")
        self.btn_save_schedule.pack(side="left", padx=(0, 10))

        self.btn_open_note = ctk.CTkButton(self.button_frame, text="打开文件",
                                           command=self.app.open_note_with_editor)
        self.btn_open_note.pack(side="left", padx=(0, 10))

        self.btn_clear_schedule = ctk.CTkButton(self.button_frame, text="清除此笔记设置",
                                                command=self.clear_current_schedule,
                                                fg_color="red")
        self.btn_clear_schedule.pack(side="left")

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
        self.weekday_var.set("")
        self.hour_var.set("10")
        self.minute_var.set("30")
        self.on_unit_change()

    def hide_schedule_widgets(self):
        self.label_mode.grid_forget()
        self.mode_frame.grid_forget()
        self.label_rule_header.grid_forget()
        self.rule_builder_frame.grid_forget()
        self.weekday_frame.grid_forget()
        self.time_frame.grid_forget()
        self.button_frame.grid_forget()

    def show_schedule_widgets(self):
        self.label_mode.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        self.mode_frame.grid(row=2, column=0, columnspan=4, padx=10, pady=5, sticky="w")
        self.label_rule_header.grid(row=3, column=0, columnspan=2, padx=10, pady=(10, 0), sticky="w")
        self.rule_builder_frame.grid(row=4, column=0, columnspan=4, padx=10, pady=0, sticky="w")
        self.on_unit_change()
        self.button_frame.grid(row=7, column=0, columnspan=4, padx=10, pady=20, sticky="w")

    def on_unit_change(self, selected_unit=None):
        if selected_unit is None:
            selected_unit = self.unit_var.get()

        if selected_unit == "周":
            self.weekday_frame.grid(row=5, column=0, columnspan=4, padx=10, pady=5, sticky="w")
            self.time_frame.grid(row=6, column=0, columnspan=4, padx=10, pady=5, sticky="w")
        elif selected_unit == "天":
            self.weekday_frame.grid_forget()
            self.time_frame.grid(row=6, column=0, columnspan=4, padx=10, pady=5, sticky="w")
        else:
            self.weekday_frame.grid_forget()
            self.time_frame.grid_forget()

    def parse_and_load_schedule_rule(self, schedule_info):
        """解析存储的规则字符串并更新GUI"""
        if not schedule_info or "schedule" not in schedule_info:
            self.reset_schedule_gui()
            return

        self.mode_var.set(schedule_info.get("mode", "light"))
        rule = schedule_info.get("schedule", "")

        interval_match = re.search(r"every\((\d*)\)", rule)
        self.interval_var.set(interval_match.group(1) if interval_match and interval_match.group(1) else "1")

        unit_match = re.search(r"\.(" + "|".join(self.unit_map.values()) + r")", rule)
        if unit_match and unit_match.group(1) in self.unit_map_rev:
            self.unit_var.set(self.unit_map_rev[unit_match.group(1)])
        else:
            unit_match_singular = re.search(r"\.(minute|hour|day|week)", rule)
            if unit_match_singular:
                singular_unit = unit_match_singular.group(1)
                plural_unit = singular_unit + 's' if singular_unit not in ['day', 'week'] else singular_unit + ('s' if singular_unit == 'week' else 's')
                if plural_unit in self.unit_map_rev:
                    self.unit_var.set(self.unit_map_rev[plural_unit])
                else:
                    self.unit_var.set("天")
            else:
                self.unit_var.set("天")

        weekday_match = re.search(r"\.(" + "|".join(self.weekday_map.values()) + r")", rule)
        if weekday_match and weekday_match.group(1) in self.weekday_map_rev:
            self.weekday_var.set(self.weekday_map_rev[weekday_match.group(1)])
        else:
            self.weekday_var.set("")

        time_match = re.search(r"at\(['\"](\d{1,2}:\d{2})['\"]\)", rule)
        if time_match:
            hour, minute = time_match.group(1).split(":")
            self.hour_var.set(f"{int(hour):02d}")
            self.minute_var.set(f"{int(minute):02d}")
        else:
            self.hour_var.set("10")
            self.minute_var.set("30")

        self.on_unit_change()

    def save_current_schedule(self):
        if not self.app.selected_note:
            messagebox.showwarning("警告", "请先从左侧选择一个笔记。")
            return

        try:
            interval = int(self.interval_var.get())
            if interval <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("警告", "频率间隔必须是一个正整数。")
            return

        unit_key = self.unit_var.get()
        unit_val = self.unit_map[unit_key]

        rule_parts = [f"every({interval if interval > 1 else ''})", f".{unit_val}"]

        if unit_key == "周":
            weekday_key = self.weekday_var.get()
            if not weekday_key:
                messagebox.showwarning("警告", "选择“周”为单位时，必须选择具体是周几。")
                return
            rule_parts.append(f".{self.weekday_map[weekday_key]}")

        if unit_key in ["天", "周"]:
            hour = self.hour_var.get()
            minute = self.minute_var.get()
            rule_parts.append(f".at('{hour}:{minute}')")

        schedule_info = {"mode": self.mode_var.get(), "schedule": "".join(rule_parts)}
        self.app.config_manager.set_note_schedule(self.app.selected_note, schedule_info)
        self.app._update_listbox_colors()
        self.app.scheduler_service.reload_schedules()

    def clear_current_schedule(self):
        if not self.app.selected_note:
            messagebox.showwarning("警告", "请先从左侧选择一个笔记。")
            return

        if messagebox.askyesno("确认", f"确定要清除 '{self.app.selected_note}' 的所有提醒设置吗？"):
            self.app.config_manager.set_note_schedule(self.app.selected_note, None)
            self.reset_schedule_gui()
            self.app._update_listbox_colors()
            self.app.scheduler_service.reload_schedules()
