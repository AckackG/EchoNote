#!/user/bin/env python3
# -*- coding: utf-8 -*-
import re
from tkinter import messagebox
import customtkinter as ctk


# 用于显示鼠标悬浮提示的辅助类
class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event):
        if self.tooltip_window or not self.text:
            return
        # 计算 tooltip 的位置
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        # 创建一个顶层窗口作为 tooltip
        self.tooltip_window = ctk.CTkToplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)  # 无边框
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

        label = ctk.CTkLabel(self.tooltip_window, text=self.text,
                             font=("Segoe UI", 18),
                             fg_color="#CCCCCC",
                             corner_radius=4,
                             padx=5, pady=3)
        label.pack()

    def hide_tooltip(self, event):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


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
        self.mode_var = ctk.StringVar(value="popup")

        self.mode_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.radio_popup = ctk.CTkRadioButton(self.mode_frame, text="直接显示", variable=self.mode_var,
                                              value="popup")
        self.radio_popup.pack(side="left", padx=(10, 5), pady=5)
        self.radio_light = ctk.CTkRadioButton(self.mode_frame, text="系统通知", variable=self.mode_var,
                                              value="light")
        self.radio_light.pack(side="left", padx=5, pady=5)

        Tooltip(self.radio_light, text="通过操作系统发送一条可点击的通知消息，持续60秒。")
        Tooltip(self.radio_popup, text="直接使用设置好的编辑器打开对应的笔记文件。")

        # --- 调度规则构建器 ---
        self.label_rule_header = ctk.CTkLabel(self, text="提醒规则:")
        self.rule_builder_frame = ctk.CTkFrame(self, fg_color="transparent")

        self.label_every = ctk.CTkLabel(self.rule_builder_frame, text="每")
        self.interval_var = ctk.StringVar(value="1")
        self.entry_interval = ctk.CTkEntry(self.rule_builder_frame, textvariable=self.interval_var, width=50)

        self.unit_map = {"分钟": "minutes", "小时": "hours", "天": "days", "周": "weeks"}
        self.unit_map_rev = {v: k for k, v in self.unit_map.items()}
        self.unit_var = ctk.StringVar(value="周")
        self.option_unit = ctk.CTkOptionMenu(self.rule_builder_frame, variable=self.unit_var,
                                             values=list(self.unit_map.keys()), command=self.on_unit_change)

        self.weekday_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.label_weekday = ctk.CTkLabel(self.weekday_frame, text="在:")
        self.weekday_map = {"周一": "monday", "周二": "tuesday", "周三": "wednesday", "周四": "thursday",
                            "周五": "friday", "周六": "saturday", "周日": "sunday"}
        self.weekday_map_rev = {v: k for k, v in self.weekday_map.items()}

        self.weekday_vars = {day_en: ctk.BooleanVar() for day_en in self.weekday_map.values()}
        weekday_checkbox_frame = ctk.CTkFrame(self.weekday_frame, fg_color="transparent")
        col = 0
        for day_cn, day_en in self.weekday_map.items():
            cb = ctk.CTkCheckBox(weekday_checkbox_frame, text=day_cn, variable=self.weekday_vars[day_en])
            cb.grid(row=0, column=col, padx=4, pady=5)
            col += 1

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

        self.btn_smart_analyze = ctk.CTkButton(self.button_frame, text="智能分析",
                                               command=self.run_smart_analysis)
        self.btn_smart_analyze.pack(side="left", padx=(0, 10))

        self.btn_clear_schedule = ctk.CTkButton(self.button_frame, text="清除此笔记设置",
                                                command=self.clear_current_schedule,
                                                fg_color="red")
        self.btn_clear_schedule.pack(side="left")

        # --- 布局规则构建器 ---
        self.label_every.grid(row=0, column=0, padx=(0, 5), pady=5)
        self.entry_interval.grid(row=0, column=1, padx=5, pady=5)
        self.option_unit.grid(row=0, column=2, padx=5, pady=5)

        self.label_weekday.grid(row=0, column=0, padx=(0, 10), pady=5)
        weekday_checkbox_frame.grid(row=0, column=1, padx=0, pady=5)

        self.label_at.grid(row=0, column=0, padx=(0, 10), pady=5)
        self.option_hour.grid(row=0, column=1, padx=0, pady=5)
        self.label_time_sep.grid(row=0, column=2, padx=5, pady=5)
        self.option_minute.grid(row=0, column=3, padx=0, pady=5)

    def run_smart_analysis(self):
        """执行智能分析：计算、显示任务分布图并推荐空闲时间点"""
        grid = self.app.task_analyzer.analyze_weekly_schedule()
        self._show_analysis_window(grid)
        day_en, hour_str = self.app.task_analyzer.find_least_busy_slot(grid)

        self.reset_schedule_gui()
        self.unit_var.set("周")
        for var in self.weekday_vars.values():
            var.set(False)
        self.weekday_vars[day_en].set(True)
        self.hour_var.set(hour_str)
        self.minute_var.set("30")

        self.on_unit_change()

    def _show_analysis_window(self, grid_data):
        """创建一个新窗口来显示任务分布热力图"""
        win = ctk.CTkToplevel(self)
        win.title("任务分布热力图")
        win.geometry("540x320")
        win.transient(self.app)
        win.grab_set()

        main_frame = ctk.CTkFrame(win)
        main_frame.pack(padx=10, pady=10, fill="both", expand=True)

        days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        # 新的表头，明确表示时间范围
        headers = ["非工作", "8-9", "9-10", "10-11", "午休", "15-16", "16-17", "17-18"]
        # 为每个列定义宽度
        column_widths = [60, 40, 40, 40, 60, 40, 40, 40]

        # 创建时间表头
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(main_frame, text=header, font=("Segoe UI", 10), width=column_widths[i])
            label.grid(row=0, column=i + 1, padx=1, pady=1)

        # 创建星期表头
        for i, day in enumerate(days):
            label = ctk.CTkLabel(main_frame, text=day, font=("Segoe UI", 12))
            label.grid(row=i + 1, column=0, padx=5, pady=2, sticky="e")

        # 创建热力图的单元格
        for day_idx in range(7):
            for col_idx in range(len(headers)):
                count = grid_data[day_idx][col_idx]
                color = self._get_color_for_value(count)

                cell_frame = ctk.CTkFrame(main_frame, fg_color=color, width=column_widths[col_idx], height=30,
                                          corner_radius=3, border_width=0)
                cell_frame.grid(row=day_idx + 1, column=col_idx + 1, padx=1, pady=1)
                cell_frame.grid_propagate(False)

                label = ctk.CTkLabel(cell_frame, text=str(count), fg_color="transparent",
                                     font=("Segoe UI", 10), text_color="black")
                label.place(relx=0.5, rely=0.5, anchor="center")

    def _get_color_for_value(self, value):
        """根据任务数返回不同的颜色，用于热力图"""
        if value == 0:
            return "#606060"  # 灰色
        elif value == 1:
            return "#5D9C59"  # 绿色
        elif value == 2:
            return "#F0C808"  # 黄色
        elif value == 3:
            return "#E57373"  # 粉色
        else:  # 4 及以上
            return "#C62828"  # 深红色

    def reset_schedule_gui(self):
        """将调度GUI重置为默认状态"""
        self.mode_var.set("popup")
        self.interval_var.set("1")
        self.unit_var.set("周")
        # 清空所有星期复选框
        for var in self.weekday_vars.values():
            var.set(False)
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
            self.label_every.grid_forget()
            self.entry_interval.grid_forget()
            self.interval_var.set("1")
            self.weekday_frame.grid(row=5, column=0, columnspan=4, padx=10, pady=5, sticky="w")
            self.time_frame.grid(row=6, column=0, columnspan=4, padx=10, pady=5, sticky="w")
        elif selected_unit == "天":
            self.label_every.grid(row=0, column=0, padx=(0, 5), pady=5)
            self.entry_interval.grid(row=0, column=1, padx=5, pady=5)
            self.weekday_frame.grid_forget()
            self.time_frame.grid(row=6, column=0, columnspan=4, padx=10, pady=5, sticky="w")
        else:  # 分钟, 小时
            self.label_every.grid(row=0, column=0, padx=(0, 5), pady=5)
            self.entry_interval.grid(row=0, column=1, padx=5, pady=5)
            self.weekday_frame.grid_forget()
            self.time_frame.grid_forget()

    def parse_and_load_schedule_rule(self, schedule_info):
        """解析存储的规则字符串或列表并更新GUI"""
        self.reset_schedule_gui()

        if not schedule_info or "schedule" not in schedule_info:
            return

        self.mode_var.set(schedule_info.get("mode", "popup"))
        rule = schedule_info.get("schedule", "")

        if isinstance(rule, list) and rule:
            self.unit_var.set("周")
            self.interval_var.set("1")

            time_match = re.search(r"at\(['\"](\d{1,2}:\d{2})['\"]\)", rule[0])
            if time_match:
                hour, minute = time_match.group(1).split(":")
                self.hour_var.set(f"{int(hour):02d}")
                self.minute_var.set(f"{int(minute):02d}")

            for sub_rule in rule:
                for day_en in self.weekday_map.values():
                    if f".{day_en}" in sub_rule:
                        self.weekday_vars[day_en].set(True)

        elif isinstance(rule, str) and rule:
            interval_match = re.search(r"every\((\d*)\)", rule)
            self.interval_var.set(interval_match.group(1) if interval_match and interval_match.group(1) else "1")

            unit_match = re.search(r"\.(" + "|".join(self.unit_map.values()) + r")", rule)
            if unit_match and unit_match.group(1) in self.unit_map_rev:
                self.unit_var.set(self.unit_map_rev[unit_match.group(1)])
            else:
                self.unit_var.set("天")

            if self.unit_var.get() == "周":
                weekday_match = re.search(r"\.(" + "|".join(self.weekday_map.values()) + r")", rule)
                if weekday_match and weekday_match.group(1) in self.weekday_map_rev:
                    self.weekday_vars[weekday_match.group(1)].set(True)

            time_match = re.search(r"at\(['\"](\d{1,2}:\d{2})['\"]\)", rule)
            if time_match:
                hour, minute = time_match.group(1).split(":")
                self.hour_var.set(f"{int(hour):02d}")
                self.minute_var.set(f"{int(minute):02d}")
        else:
            return

        self.on_unit_change()

    def save_current_schedule(self):
        if not self.app.selected_note:
            messagebox.showwarning("警告", "请先从左侧选择一个笔记。")
            return

        unit_key = self.unit_var.get()

        if unit_key != "周":
            try:
                interval = int(self.interval_var.get())
                if interval <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("警告", "频率间隔必须是一个正整数。")
                return
        else:
            interval = 1

        if unit_key == "周":
            selected_weekdays = [day_en for day_en, var in self.weekday_vars.items() if var.get()]
            if not selected_weekdays:
                messagebox.showwarning("警告", "选择“周”为单位时，必须选择至少一个星期几。")
                return

            hour = self.hour_var.get()
            minute = self.minute_var.get()
            time_part = f".at('{hour}:{minute}')"

            rules = [f"every().{day_en}{time_part}" for day_en in selected_weekdays]
            schedule_info = {"mode": self.mode_var.get(), "schedule": rules}
        else:
            unit_val = self.unit_map[unit_key]
            rule_parts = [f"every({interval if interval > 1 else ''})", f".{unit_val}"]

            if unit_key == "天":
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