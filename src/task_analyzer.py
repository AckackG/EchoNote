#!/user/bin/env python3
# -*- coding: utf-8 -*-
import re


class TaskAnalyzer:
    """负责分析所有笔记的调度任务，并提供建议"""

    # 将一天划分为8个时间段
    TIME_SLOTS = 8
    # 上午工作时段的列索引
    MORNING_SLOTS = [1, 2, 3]
    # 下午工作时段的列索引
    AFTERNOON_SLOTS = [5, 6, 7]

    def __init__(self, config_manager):
        self.config_manager = config_manager
        # 星期英文到索引的映射 (周一=0)
        self.weekday_map = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }

    def _map_hour_to_column(self, hour: int) -> int:
        """将24小时制的小时映射到8个时间段的列索引"""
        if 8 <= hour < 11:  # 上午工作时间 (8, 9, 10)
            return hour - 8 + 1  # 映射到 1, 2, 3
        elif 15 <= hour < 18:  # 下午工作时间 (15, 16, 17)
            return hour - 15 + 5  # 映射到 5, 6, 7
        elif 11 <= hour < 15:  # 午休时间 (11, 12, 13, 14)
            return 4  # 映射到 4
        else:  # 其他非工作时间
            return 0  # 映射到 0

    def _map_column_to_hour(self, column: int) -> str:
        """将列索引反向映射回一个代表性的小时"""
        if column in self.MORNING_SLOTS:  # 上午
            return f"{column - 1 + 8:02d}"
        elif column in self.AFTERNOON_SLOTS:  # 下午
            return f"{column - 5 + 15:02d}"
        elif column == 4:  # 午休
            return "12"
        else:  # 非工作
            return "20"

    def analyze_weekly_schedule(self):
        """
        分析所有已配置的调度任务，返回一个 7x8 的二维列表。
        :return: list[list[int]] 7天 x 8个时间段的任务计数网格
        """
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
        在任务网格中寻找最空闲的时间点，按优先级搜索。
        :param grid: 7x8 的任务计数网格
        :return: tuple (建议的星期几英文名, 建议的小时字符串)
        """
        weekday_map_rev = {v: k for k, v in self.weekday_map.items()}
        best_slot = None
        min_tasks = float('inf')

        # 优先级1: 搜索工作日的上午时段 (任务数 < 2)
        for day_idx in range(5):
            for col_idx in self.MORNING_SLOTS:
                if grid[day_idx][col_idx] < 2 and grid[day_idx][col_idx] < min_tasks:
                    min_tasks = grid[day_idx][col_idx]
                    best_slot = (weekday_map_rev[day_idx], self._map_column_to_hour(col_idx))
        if best_slot:
            return best_slot

        # 优先级2: 搜索工作日的下午时段 (任务数 < 2)
        min_tasks = float('inf')
        for day_idx in range(5):
            for col_idx in self.AFTERNOON_SLOTS:
                if grid[day_idx][col_idx] < 2 and grid[day_idx][col_idx] < min_tasks:
                    min_tasks = grid[day_idx][col_idx]
                    best_slot = (weekday_map_rev[day_idx], self._map_column_to_hour(col_idx))
        if best_slot:
            return best_slot

        # 最终备选: 在所有时间里寻找任务最少的那个
        min_tasks = float('inf')
        # 默认值，以防万一所有格子任务数都一样多
        best_slot = ("monday", "10")
        for day_idx in range(7):
            for col_idx in range(self.TIME_SLOTS):
                if grid[day_idx][col_idx] < min_tasks:
                    min_tasks = grid[day_idx][col_idx]
                    best_slot = (weekday_map_rev[day_idx], self._map_column_to_hour(col_idx))

        return best_slot