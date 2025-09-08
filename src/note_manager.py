#!/user/bin/env python3
# -*- coding: utf-8 -*-
import os
from loguru import logger


class NoteManager:
    """负责扫描和管理数据文件夹中的笔记文件"""
    SUPPORTED_IMG_EXTS = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
    SUPPORTED_MD_EXTS = ['.md', '.markdown']

    def __init__(self, data_folder):
        self.data_folder = data_folder
        self.notes = []

    def scan_notes(self):
        """扫描数据文件夹，加载所有支持的笔记文件"""
        self.notes = []
        if not self.data_folder or not os.path.isdir(self.data_folder):
            logger.warning(f"数据文件夹 '{self.data_folder}' 不存在或未设置。")
            return []

        logger.info(f"开始扫描笔记文件夹: {self.data_folder}")
        for filename in os.listdir(self.data_folder):
            file_path = os.path.join(self.data_folder, filename)
            if os.path.isfile(file_path):
                _, ext = os.path.splitext(filename)
                if ext.lower() in self.SUPPORTED_MD_EXTS or ext.lower() in self.SUPPORTED_IMG_EXTS:
                    self.notes.append(filename)

        self.notes.sort()
        logger.info(f"扫描完成，共找到 {len(self.notes)} 个笔记。")
        return self.notes

    def get_note_type(self, filename):
        """根据文件名后缀判断笔记类型"""
        _, ext = os.path.splitext(filename)
        if ext.lower() in self.SUPPORTED_MD_EXTS:
            return 'markdown'
        elif ext.lower() in self.SUPPORTED_IMG_EXTS:
            return 'image'
        return 'unknown'