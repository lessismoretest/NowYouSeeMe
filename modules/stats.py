import logging
import time
from datetime import datetime
from rich.logging import RichHandler
import os
import json
from collections import defaultdict, deque

# 设置日志
if not os.path.exists('logs'):
    os.makedirs('logs')

log_file = f"logs/stats_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        RichHandler(rich_tracebacks=True),
        logging.FileHandler(log_file)
    ]
)
logger = logging.getLogger("stats")

class StatsTracker:
    """
    统计跟踪器，用于记录和分析手势和表情的统计数据
    """
    def __init__(self):
        """
        初始化统计跟踪器
        """
        # 总计数器
        self.gesture_counts = defaultdict(int)
        self.expression_counts = defaultdict(int)
        
        # 时间窗口计数器（用于计算频率）
        self.window_size = 60  # 60秒窗口
        self.gesture_history = defaultdict(lambda: deque(maxlen=100))  # 存储最近100个事件的时间戳
        self.expression_history = defaultdict(lambda: deque(maxlen=100))
        
        # 会话开始时间
        self.session_start_time = time.time()
        
        # 统计数据文件
        self.stats_dir = 'stats'
        if not os.path.exists(self.stats_dir):
            os.makedirs(self.stats_dir)
        
        self.stats_file = os.path.join(self.stats_dir, f'stats_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        
        logger.info("统计跟踪器初始化完成")
    
    def record_gestures(self, gestures):
        """
        记录手势
        
        @param {list} gestures - 检测到的手势列表
        """
        current_time = time.time()
        
        for gesture in gestures:
            # 增加总计数
            self.gesture_counts[gesture] += 1
            
            # 记录时间戳用于频率计算
            self.gesture_history[gesture].append(current_time)
    
    def record_expressions(self, expressions):
        """
        记录面部表情
        
        @param {list} expressions - 检测到的表情列表
        """
        current_time = time.time()
        
        for expression in expressions:
            # 增加总计数
            self.expression_counts[expression] += 1
            
            # 记录时间戳用于频率计算
            self.expression_history[expression].append(current_time)
    
    def get_gesture_frequency(self, gesture):
        """
        获取特定手势的频率（每分钟次数）
        
        @param {str} gesture - 手势名称
        @returns {float} 每分钟频率
        """
        if gesture not in self.gesture_history or not self.gesture_history[gesture]:
            return 0.0
        
        current_time = time.time()
        # 过滤出窗口内的时间戳
        recent_timestamps = [ts for ts in self.gesture_history[gesture] if current_time - ts <= self.window_size]
        
        if not recent_timestamps:
            return 0.0
        
        # 计算频率（每分钟次数）
        return len(recent_timestamps) * (60 / self.window_size)
    
    def get_expression_frequency(self, expression):
        """
        获取特定表情的频率（每分钟次数）
        
        @param {str} expression - 表情名称
        @returns {float} 每分钟频率
        """
        if expression not in self.expression_history or not self.expression_history[expression]:
            return 0.0
        
        current_time = time.time()
        # 过滤出窗口内的时间戳
        recent_timestamps = [ts for ts in self.expression_history[expression] if current_time - ts <= self.window_size]
        
        if not recent_timestamps:
            return 0.0
        
        # 计算频率（每分钟次数）
        return len(recent_timestamps) * (60 / self.window_size)
    
    def get_stats(self):
        """
        获取所有统计数据
        
        @returns {dict} 统计数据
        """
        session_duration = time.time() - self.session_start_time
        minutes = session_duration / 60
        
        stats = {
            "session_duration": {
                "seconds": round(session_duration, 1),
                "minutes": round(minutes, 1),
                "hours": round(minutes / 60, 2)
            },
            "gestures": {
                "counts": dict(self.gesture_counts),
                "frequencies": {}
            },
            "expressions": {
                "counts": dict(self.expression_counts),
                "frequencies": {}
            }
        }
        
        # 计算频率
        for gesture in self.gesture_counts:
            stats["gestures"]["frequencies"][gesture] = round(self.get_gesture_frequency(gesture), 1)
        
        for expression in self.expression_counts:
            stats["expressions"]["frequencies"][expression] = round(self.get_expression_frequency(expression), 1)
        
        return stats
    
    def save_stats(self):
        """
        保存统计数据到文件
        """
        try:
            stats = self.get_stats()
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            logger.info(f"统计数据已保存到 {self.stats_file}")
            return True
        except Exception as e:
            logger.error(f"保存统计数据时出错: {str(e)}")
            return False
    
    def reset(self):
        """
        重置统计数据
        """
        # 保存当前统计数据
        self.save_stats()
        
        # 重置计数器
        self.gesture_counts = defaultdict(int)
        self.expression_counts = defaultdict(int)
        self.gesture_history = defaultdict(lambda: deque(maxlen=100))
        self.expression_history = defaultdict(lambda: deque(maxlen=100))
        self.session_start_time = time.time()
        
        # 创建新的统计文件
        self.stats_file = os.path.join(self.stats_dir, f'stats_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        
        logger.info("统计数据已重置") 