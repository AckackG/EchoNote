#!/user/bin/env python3
# -*- coding: utf-8 -*-
import re


class TaskAnalyzer:
    """负责分析所有笔记的调度任务，并提供建议"""

    def __init__(self, config_manager):
        self.config_manager = config_manager
        # 星期英文到索引的映射 (周一=0)
        self.weekday_map = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }

    def analyze_weekly_schedule(self):
        """
        分析所有已配置的调度任务，返回一个 7x24 的二维列表，代表一周内每小时的任务数。
        :return: list[list[int]] 7天 x 24小时的任务计数网格
        """
        # 初始化网格: grid[星期几索引][小时] = 任务数
        grid = [[0] * 24 for _ in range(7)]
        all_schedules = self.config_manager.config.get('notes_schedule', {})

        for schedule_info in all_schedules.values():
            rules = schedule_info.get("schedule")
            if not rules:
                continue

            # 统一将规则处理为列表，以兼容新旧格式
            if isinstance(rules, str):
                rules = [rules]

            for rule in rules:
                # 只分析包含具体执行时间的 "at()" 规则
                time_match = re.search(r"at\(['\"](\d{1,2}):\d{2}['\"]\)", rule)
                if not time_match:
                    continue

                hour = int(time_match.group(1))

                # --- 处理按周重复的规则 ---
                is_weekly = False
                for day_en, day_idx in self.weekday_map.items():
                    if f".{day_en}" in rule:
                        grid[day_idx][hour] += 1
                        is_weekly = True
                if is_weekly:
                    continue

                # --- 处理按天重复的规则 ---
                if ".days" in rule:
                    # 每天的这个时间点任务数都+1
                    for day_idx in range(7):
                        grid[day_idx][hour] += 1

        return grid

    def find_least_busy_slot(self, grid):
        """
        在任务网格中寻找最空闲的时间点。
        会优先考虑工作日（周一至周五）的上班时间（9点到17点）。
        :param grid: 7x24 的任务计数网格
        :return: tuple (建议的星期几英文名, 建议的小时字符串)
        """
        min_tasks = float('inf')
        best_slot = ("monday", "10")  # 提供一个默认的备用值

        # 索引到星期英文的逆向映射
        weekday_map_rev = {v: k for k, v in self.weekday_map.items()}

        # 优先级1: 搜索工作日的上班时间 (周一到周五, 9:00 - 17:00)
        for day_idx in range(5):  # 0=周一, 4=周五
            for hour in range(9, 18):  # 9点到17点
                if grid[day_idx][hour] < min_tasks:
                    min_tasks = grid[day_idx][hour]
                    best_slot = (weekday_map_rev[day_idx], f"{hour:02d}")

        # 如果上班时间都有任务，则扩大搜索范围到所有时间
        if min_tasks > 0:
            for day_idx in range(7):
                for hour in range(24):
                    if grid[day_idx][hour] < min_tasks:
                        min_tasks = grid[day_idx][hour]
                        best_slot = (weekday_map_rev[day_idx], f"{hour:02d}")

        return best_slot