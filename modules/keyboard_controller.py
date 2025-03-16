import pyautogui
import logging
import os
from datetime import datetime
from rich.logging import RichHandler
import time

# 设置日志
if not os.path.exists('logs'):
    os.makedirs('logs')

log_file = f"logs/keyboard_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        RichHandler(rich_tracebacks=True),
        logging.FileHandler(log_file)
    ]
)
logger = logging.getLogger("keyboard")

class KeyboardController:
    """
    键盘控制器类，用于模拟键盘操作
    """
    def __init__(self):
        """
        初始化键盘控制器
        """
        # 快捷键映射
        self.shortcuts = {
            "zoom_in": {"keys": ["command", "+"], "description": "放大"},
            "zoom_out": {"keys": ["command", "-"], "description": "缩小"},
            "copy": {"keys": ["command", "c"], "description": "复制"},
            "paste": {"keys": ["command", "v"], "description": "粘贴"},
            "cut": {"keys": ["command", "x"], "description": "剪切"},
            "save": {"keys": ["command", "s"], "description": "保存"},
            "undo": {"keys": ["command", "z"], "description": "撤销"},
            "redo": {"keys": ["command", "shift", "z"], "description": "重做"}
        }
        
        # 快捷键冷却时间（秒）
        self.cooldown = 0.5
        self.last_shortcut_time = {}
        
        logger.info("键盘控制器初始化完成")
    
    def execute_shortcut(self, shortcut_name):
        """
        执行快捷键
        
        @param {str} shortcut_name - 快捷键名称
        @returns {bool} 是否成功执行
        """
        if shortcut_name not in self.shortcuts:
            logger.warning(f"未知的快捷键: {shortcut_name}")
            return False
        
        # 检查冷却时间
        current_time = time.time()
        if shortcut_name in self.last_shortcut_time:
            time_since_last = current_time - self.last_shortcut_time[shortcut_name]
            if time_since_last < self.cooldown:
                logger.debug(f"快捷键 {shortcut_name} 冷却中，跳过执行")
                return False
        
        # 获取快捷键
        shortcut = self.shortcuts[shortcut_name]
        keys = shortcut["keys"]
        description = shortcut["description"]
        
        try:
            # 按下所有键
            for key in keys:
                pyautogui.keyDown(key)
            
            # 释放所有键（按相反顺序）
            for key in reversed(keys):
                pyautogui.keyUp(key)
            
            # 更新最后执行时间
            self.last_shortcut_time[shortcut_name] = current_time
            
            logger.info(f"执行快捷键: {shortcut_name} ({description})")
            return True
        except Exception as e:
            logger.error(f"执行快捷键 {shortcut_name} 时出错: {str(e)}")
            return False
    
    def handle_gesture(self, gesture):
        """
        处理手势并执行对应的快捷键
        
        @param {str} gesture - 手势名称
        @returns {bool} 是否成功执行
        """
        # 手势到快捷键的映射
        gesture_to_shortcut = {
            "zoom_in": "zoom_in",
            "zoom_out": "zoom_out",
            # 可以添加更多手势到快捷键的映射
        }
        
        if gesture in gesture_to_shortcut:
            shortcut_name = gesture_to_shortcut[gesture]
            return self.execute_shortcut(shortcut_name)
        else:
            logger.debug(f"手势 {gesture} 没有对应的快捷键")
            return False 