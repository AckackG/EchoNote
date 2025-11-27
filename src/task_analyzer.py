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

    def _get_slots(self):
        """从配置获取时间段设置，如果未设置则返回默认值"""
        default_slots = [
            "00:00", "08:00", "09:00", "10:00", "11:00", "12:00",
            "14:00", "15:00", "16:00", "17:00", "18:00", "20:00", "24:00"
        ]
        return self.config_manager.get_setting("analysis_slots", default_slots)

    def _time_to_minutes(self, time_str: str) -> int:
        """将 HH:MM 格式的字符串转换为从00:00开始的分钟数"""
        try:
            parts = time_str.split(':')
            h = int(parts[0])
            m = int(parts[1]) if len(parts) > 1 else 0
            # 特殊处理 24:00
            if h == 24:
                return 24 * 60
            return h * 60 + m
        except ValueError:
            return 0

    def _map_time_to_column(self, target_time_str: str, slots: list) -> int:
        """
        将目标时间映射到 slots 定义的区间索引。
        区间定义为 [slot[i], slot[i+1])
        """
        target_minutes = self._time_to_minutes(target_time_str)

        # 遍历区间，找到目标时间落在哪个区间内
        # slots 类似于 ["00:00", "08:00", ..., "24:00"]
        # 区间数量 = len(slots) - 1
        for i in range(len(slots) - 1):
            start_minutes = self._time_to_minutes(slots[i])
            end_minutes = self._time_to_minutes(slots[i + 1])

            if start_minutes <= target_minutes < end_minutes:
                return i

        # 如果超出所有定义区间（例如正好是 24:00 或配置有误），归类到最后一个区间
        return max(0, len(slots) - 2)

    def _get_slot_display_name(self, idx: int) -> str:
        """获取列索引对应的显示名称（用于推荐时）"""
        slots = self._get_slots()
        if 0 <= idx < len(slots) - 1:
            return slots[idx]  # 返回该时间段的起始时间作为推荐时间
        return "10:00"  # Fallback

    def analyze_weekly_schedule(self):
        """
        分析所有已配置的调度任务，返回一个二维列表。
        :return: (grid, headers)
                 grid: list[list[int]] 7天 x N个时间段的任务计数网格
                 headers: list[str] N个时间段的显示标题
        """
        slots = self._get_slots()
        num_slots = max(1, len(slots) - 1)

        # 初始化网格
        grid = [[0] * num_slots for _ in range(7)]

        # 生成表头
        headers = []
        for i in range(num_slots):
            headers.append(f"{slots[i]}-{slots[i + 1]}")

        all_schedules = self.config_manager.config.get('notes_schedule', {})

        for schedule_info in all_schedules.values():
            if not schedule_info.get('enable', True):
                continue

            rules = schedule_info.get("schedule")
            if not rules:
                continue

            if isinstance(rules, str):
                rules = [rules]

            for rule in rules:
                # 提取完整时间 HH:MM
                time_match = re.search(r"at\(['\"](\d{1,2}:\d{2})['\"]\)", rule)
                if not time_match:
                    continue

                time_str = time_match.group(1)
                column_idx = self._map_time_to_column(time_str, slots)

                # 检查是否为周任务 (周一至周五)
                is_weekly_task = False
                for day_en, day_idx in self.weekday_map.items():
                    if day_idx < 7 and f".{day_en}" in rule:
                        grid[day_idx][column_idx] += 1
                        is_weekly_task = True

                if is_weekly_task:
                    continue

                # 如果不是周任务，检查是否为“每1天”的日度任务
                if "every().days" in rule:
                    # 统计到每一天
                    for day_idx in range(7):
                        grid[day_idx][column_idx] += 1

        return grid, headers

    def find_least_busy_slot(self, grid):
        """
        在任务网格中寻找最空闲的时间点。
        优化逻辑：当存在多个最空闲时间段时，优先级如下：
        1. 08:15 (最高优先级)
        2. 08:00 ~ 09:00 之间的其他时间
        3. 其他时间
        :param grid: 7xN 的任务计数网格
        :return: tuple (建议的星期几英文名, 建议的小时字符串, 建议的分钟字符串)
        """
        weekday_map_rev = {v: k for k, v in self.weekday_map.items()}
        best_slot = None
        min_tasks = float('inf')

        num_cols = len(grid[0]) if grid else 0

        for day_idx in range(7):
            for col_idx in range(num_cols):
                count = grid[day_idx][col_idx]
                time_start_str = self._get_slot_display_name(col_idx)

                # 判断当前格子是否比已记录的 best_slot 更优
                is_better = False

                if count < min_tasks:
                    # 发现绝对任务数更少的格子，直接更新
                    is_better = True
                elif count == min_tasks:
                    # 任务数相同，进行偏好判断 (Tie-breaking)
                    if best_slot:
                        current_best_time = best_slot[1]

                        # 优先级 1: 如果新时间是 08:15，且当前最佳不是 08:15，则更新
                        if time_start_str == "08:15" and current_best_time != "08:15":
                            is_better = True

                        # 优先级 2: 如果新时间是 08:xx 系列，而当前最佳不是 08:xx，则更新
                        # (注意：如果当前已经是 08:15，由于上面的判断，这里不会覆盖它)
                        elif (time_start_str.startswith("08:") and
                              not current_best_time.startswith("08:") and
                              current_best_time != "08:15"):
                            is_better = True
                    else:
                        is_better = True

                if is_better:
                    min_tasks = count
                    best_slot = (weekday_map_rev[day_idx], time_start_str)

        # 格式化返回值
        if best_slot:
            try:
                parts = best_slot[1].split(':')
                return (best_slot[0], parts[0], parts[1])
            except:
                return (best_slot[0], "08", "15")

        # 默认兜底返回值
        return ("monday", "08", "15")
