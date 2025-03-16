import pygame
import random
import numpy as np
import logging
from datetime import datetime
from rich.logging import RichHandler
import os
import time
from modules.sound_manager import SoundManager

# 设置日志
if not os.path.exists('logs'):
    os.makedirs('logs')

log_file = f"logs/snake_game_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        RichHandler(rich_tracebacks=True),
        logging.FileHandler(log_file)
    ]
)
logger = logging.getLogger("snake_game")

class SnakeGame:
    """
    贪吃蛇游戏类，使用食指控制蛇的移动方向
    """
    def __init__(self, width=640, height=480, cell_size=20):
        """
        初始化贪吃蛇游戏
        
        @param {int} width - 游戏窗口宽度
        @param {int} height - 游戏窗口高度
        @param {int} cell_size - 网格单元大小
        """
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.grid_width = width // cell_size
        self.grid_height = height // cell_size
        
        # 初始化Pygame
        pygame.init()
        self.screen = pygame.Surface((width, height))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Arial', 24)
        
        # 初始化音效管理器
        self.sound_manager = SoundManager()
        
        # 游戏状态
        self.reset()
        
        # 颜色定义
        self.colors = {
            'background': (0, 0, 0),
            'snake_head': (0, 255, 0),
            'snake_body': (0, 200, 0),
            'food': (255, 0, 0),
            'text': (255, 255, 255),
            'grid': (50, 50, 50)
        }
        
        # 方向映射
        self.directions = {
            'up': (0, -1),
            'down': (0, 1),
            'left': (-1, 0),
            'right': (1, 0)
        }
        
        # 当前方向
        self.direction = self.directions['right']
        
        # 游戏速度（帧率）
        self.fps = 10
        
        # 手势控制相关
        self.gesture_cooldown = 0
        self.gesture_cooldown_frames = 5  # 手势冷却帧数
        
        # 上一次方向
        self.last_direction = self.direction
        
        logger.info("贪吃蛇游戏初始化完成")
    
    def reset(self):
        """
        重置游戏状态
        """
        # 蛇的初始位置（中心）
        self.snake = [
            (self.grid_width // 2, self.grid_height // 2),
            (self.grid_width // 2 - 1, self.grid_height // 2),
            (self.grid_width // 2 - 2, self.grid_height // 2)
        ]
        
        # 食物位置
        self.spawn_food()
        
        # 分数
        self.score = 0
        
        # 游戏是否结束
        self.game_over = False
        
        # 游戏是否暂停
        self.paused = False
        
        # 播放开始音效
        self.sound_manager.play('start')
        
        logger.info("游戏已重置")
    
    def spawn_food(self):
        """
        在随机位置生成食物
        """
        while True:
            # 随机生成食物位置
            self.food = (
                random.randint(0, self.grid_width - 1),
                random.randint(0, self.grid_height - 1)
            )
            
            # 确保食物不会出现在蛇身上
            if self.food not in self.snake:
                break
        
        logger.info(f"食物生成在位置: {self.food}")
    
    def update(self):
        """
        更新游戏状态
        """
        if self.game_over or self.paused:
            return
        
        # 减少手势冷却时间
        if self.gesture_cooldown > 0:
            self.gesture_cooldown -= 1
        
        # 移动蛇头
        head_x, head_y = self.snake[0]
        dir_x, dir_y = self.direction
        new_head = ((head_x + dir_x) % self.grid_width, (head_y + dir_y) % self.grid_height)
        
        # 检查是否撞到自己
        if new_head in self.snake:
            self.game_over = True
            logger.info("游戏结束：蛇撞到了自己")
            self.sound_manager.play('game_over')
            return
        
        # 移动蛇
        self.snake.insert(0, new_head)
        
        # 检查是否吃到食物
        if new_head == self.food:
            self.score += 1
            self.spawn_food()
            # 播放吃食物音效
            self.sound_manager.play('eat')
            # 蛇变长（不删除尾部）
        else:
            # 删除尾部
            self.snake.pop()
    
    def handle_gesture(self, gesture, finger_direction):
        """
        处理手势输入
        
        @param {str} gesture - 识别到的手势
        @param {tuple} finger_direction - 食指方向向量 (dx, dy)
        """
        # 如果游戏已结束或暂停，只处理特定手势
        if self.game_over:
            if gesture == "fist":
                self.reset()
                self.gesture_cooldown = self.gesture_cooldown_frames * 2
                logger.info("游戏重新开始")
            return
        
        if self.paused and gesture != "palm":
            return
        
        # 手势冷却中，不处理新手势
        if self.gesture_cooldown > 0:
            self.gesture_cooldown -= 1
            return
        
        # 处理手势
        if gesture == "palm":
            # 手掌手势暂停/继续游戏
            self.paused = not self.paused
            self.gesture_cooldown = self.gesture_cooldown_frames * 2  # 更长的冷却时间
            logger.info(f"游戏{'暂停' if self.paused else '继续'}")
            # 播放暂停/继续音效
            self.sound_manager.play('pause' if self.paused else 'resume')
            return
        
        # 如果游戏暂停，不处理其他输入
        if self.paused:
            return
        
        # 处理食指方向
        if finger_direction:
            dx, dy = finger_direction
            
            # 记录当前方向用于调试
            logger.debug(f"收到方向向量: dx={dx:.2f}, dy={dy:.2f}")
            
            # 保存上一次方向
            old_direction = self.direction
            
            # 确定主要方向
            if abs(dx) > abs(dy):
                # 水平方向为主
                if dx > 0 and self.direction != self.directions['left']:
                    self.direction = self.directions['right']
                    logger.debug("向右移动")
                elif dx < 0 and self.direction != self.directions['right']:
                    self.direction = self.directions['left']
                    logger.debug("向左移动")
            else:
                # 垂直方向为主
                if dy > 0 and self.direction != self.directions['up']:
                    self.direction = self.directions['down']
                    logger.debug("向下移动")
                elif dy < 0 and self.direction != self.directions['down']:
                    self.direction = self.directions['up']
                    logger.debug("向上移动")
            
            # 如果方向改变，播放方向改变音效
            if self.direction != old_direction:
                self.sound_manager.play('direction')
    
    def render(self):
        """
        渲染游戏画面
        
        @returns {numpy.ndarray} 游戏画面图像
        """
        # 清空屏幕
        self.screen.fill(self.colors['background'])
        
        # 绘制网格
        for x in range(0, self.width, self.cell_size):
            pygame.draw.line(self.screen, self.colors['grid'], (x, 0), (x, self.height))
        for y in range(0, self.height, self.cell_size):
            pygame.draw.line(self.screen, self.colors['grid'], (0, y), (self.width, y))
        
        # 绘制食物
        food_rect = pygame.Rect(
            self.food[0] * self.cell_size,
            self.food[1] * self.cell_size,
            self.cell_size,
            self.cell_size
        )
        pygame.draw.rect(self.screen, self.colors['food'], food_rect)
        
        # 绘制蛇
        for i, (x, y) in enumerate(self.snake):
            snake_rect = pygame.Rect(
                x * self.cell_size,
                y * self.cell_size,
                self.cell_size,
                self.cell_size
            )
            color = self.colors['snake_head'] if i == 0 else self.colors['snake_body']
            pygame.draw.rect(self.screen, color, snake_rect)
        
        # 绘制分数
        score_text = self.font.render(f'分数: {self.score}', True, self.colors['text'])
        self.screen.blit(score_text, (10, 10))
        
        # 如果游戏结束，显示游戏结束信息
        if self.game_over:
            game_over_text = self.font.render('游戏结束! 握拳重新开始', True, self.colors['text'])
            text_rect = game_over_text.get_rect(center=(self.width//2, self.height//2))
            self.screen.blit(game_over_text, text_rect)
        
        # 如果游戏暂停，显示暂停信息
        if self.paused:
            pause_text = self.font.render('游戏暂停', True, self.colors['text'])
            text_rect = pause_text.get_rect(center=(self.width//2, self.height//2))
            self.screen.blit(pause_text, text_rect)
        
        # 将Pygame surface转换为numpy数组
        view = pygame.surfarray.array3d(self.screen)
        view = view.transpose([1, 0, 2])  # 调整轴顺序以匹配OpenCV格式
        
        return view
    
    def get_game_info(self):
        """
        获取游戏信息
        
        @returns {dict} 游戏信息
        """
        return {
            'score': self.score,
            'game_over': self.game_over,
            'paused': self.paused,
            'snake_length': len(self.snake)
        } 