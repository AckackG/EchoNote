import json
import os
from loguru import logger

class ConfigManager:
    """负责处理应用程序的配置文件（config.json）"""
    def __init__(self, config_path='config.json'):
        self.config_path = config_path
        self.default_config = {
            "settings": {
                "data_folder": "",
                "md_editor_path": "",
                "img_editor_path": "",
                "autostart": False,
                "window_size": [900, 700]
            },
            "notes_schedule": {}
        }
        self.config = self.load_config()

    def load_config(self):
        """加载配置文件，如果文件不存在则创建一个默认的"""
        if not os.path.exists(self.config_path):
            logger.info("配置文件不存在，将创建默认配置文件。")
            self.save_config(self.default_config)
            return self.default_config
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 确保所有键都存在
                for key, value in self.default_config.items():
                    if key not in config:
                        config[key] = value
                    elif isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            if sub_key not in config[key]:
                                config[key][sub_key] = sub_value
                return config
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"加载配置文件失败: {e}。将使用默认配置。")
            return self.default_config

    def save_config(self, data=None):
        """将当前配置保存到文件"""
        if data is None:
            data = self.config
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            logger.info("配置已成功保存。")
        except IOError as e:
            logger.error(f"保存配置文件失败: {e}")

    def get_setting(self, key, default=None):
        """获取一个全局设置项"""
        return self.config['settings'].get(key, default)

    def set_setting(self, key, value):
        """设置一个全局设置项并立即保存"""
        self.config['settings'][key] = value
        self.save_config()

    def get_note_schedule(self, note_filename):
        """获取指定笔记的调度配置"""
        return self.config['notes_schedule'].get(note_filename)

    def set_note_schedule(self, note_filename, schedule_info):
        """设置指定笔记的调度配置并立即保存"""
        if schedule_info is None:
            if note_filename in self.config['notes_schedule']:
                del self.config['notes_schedule'][note_filename]
        else:
            self.config['notes_schedule'][note_filename] = schedule_info
        self.save_config()