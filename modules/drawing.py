import cv2
import numpy as np
import logging
import os
from datetime import datetime
from rich.logging import RichHandler
import time

# 设置日志
if not os.path.exists('logs'):
    os.makedirs('logs')

log_file = f"logs/drawing_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        RichHandler(rich_tracebacks=True),
        logging.FileHandler(log_file)
    ]
)
logger = logging.getLogger("drawing")

class DrawingCanvas:
    """
    绘画画布类，用于实现手势绘画功能
    """
    def __init__(self, width=640, height=480):
        """
        初始化绘画画布
        
        @param {int} width - 画布宽度
        @param {int} height - 画布高度
        """
        # 画布尺寸
        self.width = width
        self.height = height
        
        # 创建空白画布
        self.canvas = np.ones((height, width, 3), dtype=np.uint8) * 255
        
        # 绘画设置
        self.drawing_color = (0, 0, 0)  # 默认黑色
        self.brush_size = 5  # 默认画笔大小
        self.eraser_mode = False  # 橡皮擦模式
        self.eraser_size = 20  # 橡皮擦大小
        
        # 跟踪上一个点的位置
        self.prev_point = None
        
        # 手指映射
        self.finger_map = {
            "thumb": 4,       # 拇指
            "index": 8,       # 食指
            "middle": 12,     # 中指
            "ring": 16,       # 无名指
            "pinky": 20       # 小指
        }
        
        # 默认使用食指绘画
        self.drawing_finger = "index"
        
        # 是否正在绘画
        self.is_drawing = False
        
        # 绘画历史记录，用于撤销功能
        self.history = []
        self.max_history = 10  # 最大历史记录数
        
        # 保存当前画布状态
        self.save_history()
        
        logger.info("绘画画布初始化完成")
    
    def set_drawing_finger(self, finger_name):
        """
        设置用于绘画的手指
        
        @param {str} finger_name - 手指名称（thumb, index, middle, ring, pinky）
        @returns {bool} 是否成功设置
        """
        if finger_name in self.finger_map:
            self.drawing_finger = finger_name
            logger.info(f"设置绘画手指为: {finger_name}")
            return True
        else:
            logger.warning(f"未知的手指名称: {finger_name}")
            return False
    
    def get_drawing_finger_index(self):
        """
        获取用于绘画的手指索引
        
        @returns {int} 手指索引
        """
        return self.finger_map.get(self.drawing_finger, 8)  # 默认返回食指索引
    
    def set_color(self, color):
        """
        设置绘画颜色
        
        @param {tuple} color - RGB颜色元组
        """
        self.drawing_color = color
        self.eraser_mode = False
        logger.info(f"设置绘画颜色为: {color}")
    
    def set_brush_size(self, size):
        """
        设置画笔大小
        
        @param {int} size - 画笔大小
        """
        self.brush_size = max(1, size)
        logger.info(f"设置画笔大小为: {size}")
    
    def toggle_eraser(self):
        """
        切换橡皮擦模式
        
        @returns {bool} 是否开启橡皮擦模式
        """
        self.eraser_mode = not self.eraser_mode
        logger.info(f"橡皮擦模式: {'开启' if self.eraser_mode else '关闭'}")
        return self.eraser_mode
    
    def set_eraser_size(self, size):
        """
        设置橡皮擦大小
        
        @param {int} size - 橡皮擦大小
        """
        self.eraser_size = max(5, size)
        logger.info(f"设置橡皮擦大小为: {size}")
    
    def clear(self):
        """
        清空画布
        """
        # 保存当前状态到历史记录
        self.save_history()
        
        # 清空画布
        self.canvas = np.ones((self.height, self.width, 3), dtype=np.uint8) * 255
        logger.info("清空画布")
    
    def save_history(self):
        """
        保存当前画布状态到历史记录
        """
        # 复制当前画布
        canvas_copy = self.canvas.copy()
        
        # 添加到历史记录
        self.history.append(canvas_copy)
        
        # 如果历史记录超过最大数量，删除最早的记录
        if len(self.history) > self.max_history:
            self.history.pop(0)
    
    def undo(self):
        """
        撤销上一步操作
        
        @returns {bool} 是否成功撤销
        """
        if len(self.history) > 1:
            # 移除当前状态
            self.history.pop()
            
            # 恢复到上一个状态
            self.canvas = self.history[-1].copy()
            
            logger.info("撤销上一步操作")
            return True
        else:
            logger.warning("没有可撤销的操作")
            return False
    
    def start_drawing(self, point=None):
        """
        开始绘画
        
        @param {tuple} point - 起始点坐标 (x, y)
        """
        self.is_drawing = True
        self.prev_point = point
        logger.debug("开始绘画")
    
    def stop_drawing(self):
        """
        停止绘画
        """
        if self.is_drawing:
            self.is_drawing = False
            self.prev_point = None
            
            # 保存当前状态到历史记录
            self.save_history()
            
            logger.debug("停止绘画")
    
    def draw(self, point):
        """
        在画布上绘画
        
        @param {tuple} point - 当前点坐标 (x, y)
        """
        if not self.is_drawing or point is None:
            return
        
        # 如果是第一个点，设置为上一个点
        if self.prev_point is None:
            self.prev_point = point
            return
        
        # 获取当前点和上一个点的坐标
        x1, y1 = self.prev_point
        x2, y2 = point
        
        # 确保坐标在画布范围内
        x1 = max(0, min(x1, self.width - 1))
        y1 = max(0, min(y1, self.height - 1))
        x2 = max(0, min(x2, self.width - 1))
        y2 = max(0, min(y2, self.height - 1))
        
        # 绘制线段
        if self.eraser_mode:
            # 橡皮擦模式
            cv2.line(self.canvas, (x1, y1), (x2, y2), (255, 255, 255), self.eraser_size)
        else:
            # 绘画模式
            cv2.line(self.canvas, (x1, y1), (x2, y2), self.drawing_color, self.brush_size)
        
        # 更新上一个点
        self.prev_point = point
    
    def get_canvas(self):
        """
        获取当前画布
        
        @returns {numpy.ndarray} 画布图像
        """
        return self.canvas.copy()
    
    def save_canvas(self, filename=None):
        """
        保存画布为图片
        
        @param {str} filename - 文件名，如果为None则自动生成
        @returns {str} 保存的文件路径
        """
        # 确保保存目录存在
        save_dir = 'drawings'
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        # 如果没有指定文件名，自动生成
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"drawing_{timestamp}.png"
        
        # 完整文件路径
        filepath = os.path.join(save_dir, filename)
        
        # 保存图片
        cv2.imwrite(filepath, self.canvas)
        logger.info(f"画布已保存到: {filepath}")
        
        return filepath
    
    def process_hand_landmarks(self, hand_landmarks, frame_width, frame_height):
        """
        处理手部关键点，用于绘画
        
        @param {list} hand_landmarks - 手部关键点列表
        @param {int} frame_width - 视频帧宽度
        @param {int} frame_height - 视频帧高度
        @returns {tuple} 处理后的画布和是否正在绘画
        """
        if not hand_landmarks:
            # 如果没有检测到手，停止绘画
            self.stop_drawing()
            return self.get_canvas(), False
        
        # 获取绘画手指的索引
        finger_index = self.get_drawing_finger_index()
        
        # 获取绘画手指的坐标
        finger_tip = hand_landmarks[finger_index]
        
        # 将归一化坐标转换为画布坐标
        x = int(finger_tip.x * self.width)
        y = int(finger_tip.y * self.height)
        
        # 获取食指和中指的坐标，用于判断是否绘画
        index_tip = hand_landmarks[8]
        middle_tip = hand_landmarks[12]
        
        # 计算食指和中指的距离
        distance = np.sqrt((index_tip.x - middle_tip.x) ** 2 + (index_tip.y - middle_tip.y) ** 2)
        
        # 如果食指和中指靠近，表示不绘画
        if distance < 0.05:
            self.stop_drawing()
        else:
            # 如果之前没有绘画，开始绘画
            if not self.is_drawing:
                self.start_drawing((x, y))
            else:
                # 继续绘画
                self.draw((x, y))
        
        return self.get_canvas(), self.is_drawing
    
    def overlay_on_frame(self, frame):
        """
        将画布叠加到视频帧上
        
        @param {numpy.ndarray} frame - 视频帧
        @returns {numpy.ndarray} 叠加后的视频帧
        """
        # 调整画布大小以匹配视频帧
        resized_canvas = cv2.resize(self.canvas, (frame.shape[1], frame.shape[0]))
        
        # 创建画布的掩码（白色区域为不透明，其他区域为透明）
        mask = cv2.cvtColor(resized_canvas, cv2.COLOR_BGR2GRAY)
        mask = cv2.bitwise_not(mask)  # 反转掩码
        
        # 将画布叠加到视频帧上
        result = frame.copy()
        result[mask == 0] = resized_canvas[mask == 0]
        
        return result 