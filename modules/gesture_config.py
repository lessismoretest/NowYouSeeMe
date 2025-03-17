import json
import os
import logging
from datetime import datetime
from rich.logging import RichHandler

# 设置日志
if not os.path.exists('logs'):
    os.makedirs('logs')

log_file = f"logs/gesture_config_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        RichHandler(rich_tracebacks=True),
        logging.FileHandler(log_file)
    ]
)
logger = logging.getLogger("gesture_config")

class GestureConfig:
    """
    手势配置管理类，用于管理手势与功能的映射关系
    """
    def __init__(self):
        """
        初始化手势配置管理器
        """
        # 配置文件路径
        self.config_dir = 'config'
        self.config_file = os.path.join(self.config_dir, 'gesture_config.json')
        
        # 确保配置目录存在
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        
        # 默认手势配置
        self.default_config = {
            "fist": {
                "action": "none",
                "params": {},
                "description": "无动作"
            },
            "palm": {
                "action": "none",
                "params": {},
                "description": "无动作"
            },
            "thumb_up": {
                "action": "none",
                "params": {},
                "description": "无动作"
            },
            "peace": {
                "action": "none",
                "params": {},
                "description": "无动作"
            },
            "pointing": {
                "action": "none",
                "params": {},
                "description": "无动作"
            },
            "zoom_in": {
                "action": "keyboard_shortcut",
                "params": {"shortcut": "zoom_in"},
                "description": "放大 (Command +)"
            },
            "zoom_out": {
                "action": "keyboard_shortcut",
                "params": {"shortcut": "zoom_out"},
                "description": "缩小 (Command -)"
            }
        }
        
        # 可用的动作类型
        self.available_actions = {
            "none": "无动作",
            "keyboard_shortcut": "键盘快捷键",
            "media_control": "媒体控制",
            "app_control": "应用控制",
            "custom_function": "自定义函数"
        }
        
        # 可用的键盘快捷键
        self.available_shortcuts = {
            "zoom_in": "放大 (Command +)",
            "zoom_out": "缩小 (Command -)",
            "copy": "复制 (Command C)",
            "paste": "粘贴 (Command V)",
            "cut": "剪切 (Command X)",
            "save": "保存 (Command S)",
            "undo": "撤销 (Command Z)",
            "redo": "重做 (Command Shift Z)"
        }
        
        # 加载配置
        self.config = self.load_config()
        
        logger.info("手势配置管理器初始化完成")
    
    def load_config(self):
        """
        加载手势配置
        
        @returns {dict} 手势配置
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info(f"从 {self.config_file} 加载配置成功")
                
                # 确保所有默认手势都存在于配置中
                for gesture, default_config in self.default_config.items():
                    if gesture not in config:
                        config[gesture] = default_config
                
                return config
            else:
                logger.info(f"配置文件 {self.config_file} 不存在，使用默认配置")
                return self.default_config.copy()
        except Exception as e:
            logger.error(f"加载配置时出错: {str(e)}")
            return self.default_config.copy()
    
    def save_config(self):
        """
        保存手势配置
        
        @returns {bool} 是否成功保存
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
            logger.info(f"配置已保存到 {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"保存配置时出错: {str(e)}")
            return False
    
    def get_gesture_config(self, gesture):
        """
        获取指定手势的配置
        
        @param {str} gesture - 手势名称
        @returns {dict} 手势配置
        """
        if gesture in self.config:
            return self.config[gesture]
        else:
            logger.warning(f"未知的手势: {gesture}")
            return {"action": "none", "params": {}, "description": "无动作"}
    
    def set_gesture_config(self, gesture, action, params=None, description=None):
        """
        设置指定手势的配置
        
        @param {str} gesture - 手势名称
        @param {str} action - 动作类型
        @param {dict} params - 动作参数
        @param {str} description - 动作描述
        @returns {bool} 是否成功设置
        """
        if gesture not in self.default_config:
            logger.warning(f"未知的手势: {gesture}")
            return False
        
        if action not in self.available_actions:
            logger.warning(f"未知的动作类型: {action}")
            return False
        
        if params is None:
            params = {}
        
        if description is None:
            if action == "keyboard_shortcut" and "shortcut" in params:
                shortcut = params["shortcut"]
                if shortcut in self.available_shortcuts:
                    description = self.available_shortcuts[shortcut]
                else:
                    description = f"快捷键 {shortcut}"
            else:
                description = self.available_actions[action]
        
        self.config[gesture] = {
            "action": action,
            "params": params,
            "description": description
        }
        
        # 保存配置
        self.save_config()
        
        logger.info(f"已设置手势 {gesture} 的配置: {action}, {params}, {description}")
        return True
    
    def get_all_configs(self):
        """
        获取所有手势配置
        
        @returns {dict} 所有手势配置
        """
        return self.config
    
    def get_available_actions(self):
        """
        获取可用的动作类型
        
        @returns {dict} 可用的动作类型
        """
        return self.available_actions
    
    def get_available_shortcuts(self):
        """
        获取可用的键盘快捷键
        
        @returns {dict} 可用的键盘快捷键
        """
        return self.available_shortcuts
    
    def reset_to_default(self):
        """
        重置为默认配置
        
        @returns {bool} 是否成功重置
        """
        self.config = self.default_config.copy()
        return self.save_config() 