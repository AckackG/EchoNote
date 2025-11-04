#!/user/bin/env python3
# -*- coding: utf-8 -*-
import re


class TaskAnalyzer:
    """负责分析所有笔记的调度任务，并提供建议"""

    # 将一天划分为11个时间段: 1个合并时段 + 10个工作时段
    TIME_SLOTS = 11

    def __init__(self, config_manager):
        self.config_manager = config_manager
        # 星期英文到索引的映射 (周一=0)
        self.weekday_map = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }

    def _map_hour_to_column(self, hour: int) -> int:
        """将24小时制的小时映射到11个时间段的列索引"""
        if 8 <= hour < 18:
            # 工作时间: 8点对应第1列, 9点对应第2列, ..., 17点对应第10列
            return hour - 8 + 1
        else:
            # 非工作时间 (0-7点, 18-23点) 全部映射到第0列
            return 0

    def _map_column_to_hour(self, column: int) -> str:
        """将列索引反向映射回一个代表性的小时"""
        if column == 0:
            # 对于非工作时间段，推荐一个晚上8点的时间
            return "20"
        else:
            # 对于工作时间段，还原其真实小时
            hour = column - 1 + 8
            return f"{hour:02d}"

    def analyze_weekly_schedule(self):
        """
        分析所有已配置的调度任务，返回一个 7x11 的二维列表。
        :return: list[list[int]] 7天 x 11个时间段的任务计数网格
        """
        # 初始化网格: grid[星期几索引][时间段索引] = 任务数
        grid = [[0] * self.TIME_SLOTS for _ in range(7)]
        all_schedules = self.config_manager.config.get('notes_schedule', {})

        for schedule_info in all_schedules.values():
            rules = schedule_info.get("schedule")
            if not rules:
                continue

            if isinstance(rules, str):
                rules = [rules]

            for rule in rules:
                time_match = re.search(r"at\(['\"](\d{1,2}):\d{2}['\"]\)", rule)
                if not time_match:
                    continue

                hour = int(time_match.group(1))
                column_idx = self._map_hour_to_column(hour)

                is_weekly = False
                for day_en, day_idx in self.weekday_map.items():
                    if f".{day_en}" in rule:
                        grid[day_idx][column_idx] += 1
                        is_weekly = True
                if is_weekly:
                    continue

                if ".days" in rule:
                    for day_idx in range(7):
                        grid[day_idx][column_idx] += 1

        return grid

    def find_least_busy_slot(self, grid):
        """
        在任务网格中寻找最空闲的时间点。
        优先考虑工作日（周一至周五）的工作时间段（8点到18点）。
        :param grid: 7x11 的任务计数网格
        :return: tuple (建议的星期几英文名, 建议的小时字符串)
        """
        min_tasks = float('inf')
        best_slot = ("monday", "10")  # 默认备用值

        weekday_map_rev = {v: k for k, v in self.weekday_map.items()}

        # 优先级1: 搜索工作日的工作时间 (周一到周五, 8:00 - 18:00)
        # 对应的列索引是 1 到 10
        for day_idx in range(5):  # 0=周一, 4=周五
            for col_idx in range(1, self.TIME_SLOTS):
                if grid[day_idx][col_idx] < min_tasks:
                    min_tasks = grid[day_idx][col_idx]
                    best_slot = (weekday_map_rev[day_idx], self._map_column_to_hour(col_idx))

        # 如果工作时间都有任务，则扩大搜索范围到所有时间
        if min_tasks > 0:
            for day_idx in range(7):
                for col_idx in range(self.TIME_SLOTS):
                    if grid[day_idx][col_idx] < min_tasks:
                        min_tasks = grid[day_idx][col_idx]
                        best_slot = (weekday_map_rev[day_idx], self._map_column_to_hour(col_idx))

        return best_slot