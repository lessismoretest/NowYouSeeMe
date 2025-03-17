import pyautogui
import logging
import os
from datetime import datetime
from rich.logging import RichHandler
import time
from modules.gesture_config import GestureConfig

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
        
        # 初始化手势配置
        self.gesture_config = GestureConfig()
        
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
        处理手势并执行对应的功能
        
        @param {str} gesture - 手势名称
        @returns {bool} 是否成功执行
        """
        if not gesture:
            return False
        
        # 获取手势配置
        gesture_config = self.gesture_config.get_gesture_config(gesture)
        action = gesture_config.get("action", "none")
        params = gesture_config.get("params", {})
        
        # 根据动作类型执行不同的功能
        if action == "none":
            logger.debug(f"手势 {gesture} 配置为无动作")
            return False
        elif action == "keyboard_shortcut":
            shortcut = params.get("shortcut")
            if shortcut:
                return self.execute_shortcut(shortcut)
            else:
                logger.warning(f"手势 {gesture} 的快捷键参数缺失")
                return False
        elif action == "media_control":
            # 媒体控制功能
            media_action = params.get("media_action")
            if media_action == "play_pause":
                pyautogui.press("playpause")
                logger.info("执行媒体控制: 播放/暂停")
                return True
            elif media_action == "volume_up":
                pyautogui.press("volumeup")
                logger.info("执行媒体控制: 音量增加")
                return True
            elif media_action == "volume_down":
                pyautogui.press("volumedown")
                logger.info("执行媒体控制: 音量减少")
                return True
            elif media_action == "mute":
                pyautogui.press("volumemute")
                logger.info("执行媒体控制: 静音")
                return True
            elif media_action == "next_track":
                pyautogui.press("nexttrack")
                logger.info("执行媒体控制: 下一曲")
                return True
            elif media_action == "prev_track":
                pyautogui.press("prevtrack")
                logger.info("执行媒体控制: 上一曲")
                return True
            else:
                logger.warning(f"未知的媒体控制动作: {media_action}")
                return False
        elif action == "app_control":
            # 应用控制功能
            app_action = params.get("app_action")
            if app_action == "switch_app":
                pyautogui.hotkey("command", "tab")
                logger.info("执行应用控制: 切换应用")
                return True
            elif app_action == "new_tab":
                pyautogui.hotkey("command", "t")
                logger.info("执行应用控制: 新建标签页")
                return True
            elif app_action == "close_tab":
                pyautogui.hotkey("command", "w")
                logger.info("执行应用控制: 关闭标签页")
                return True
            else:
                logger.warning(f"未知的应用控制动作: {app_action}")
                return False
        elif action == "custom_function":
            # 自定义函数功能
            function_name = params.get("function")
            if function_name == "screenshot":
                pyautogui.hotkey("command", "shift", "3")
                logger.info("执行自定义函数: 截屏")
                return True
            elif function_name == "screen_recording":
                pyautogui.hotkey("command", "shift", "5")
                logger.info("执行自定义函数: 屏幕录制")
                return True
            else:
                logger.warning(f"未知的自定义函数: {function_name}")
                return False
        else:
            logger.warning(f"未知的动作类型: {action}")
            return False
    
    def get_gesture_config(self):
        """
        获取手势配置
        
        @returns {GestureConfig} 手势配置对象
        """
        return self.gesture_config 