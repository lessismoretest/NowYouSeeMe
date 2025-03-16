import pygame
import os
import logging
from datetime import datetime
from rich.logging import RichHandler

# 设置日志
if not os.path.exists('logs'):
    os.makedirs('logs')

log_file = f"logs/sound_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        RichHandler(rich_tracebacks=True),
        logging.FileHandler(log_file)
    ]
)
logger = logging.getLogger("sound")

class SoundManager:
    """
    音效管理类，负责加载和播放游戏音效
    """
    def __init__(self):
        """
        初始化音效管理器
        """
        try:
            # 初始化pygame混音器
            pygame.mixer.init()
            
            # 创建音效目录
            if not os.path.exists('static/sounds'):
                os.makedirs('static/sounds')
            
            # 音效文件路径
            self.sounds = {
                'start': 'static/sounds/start.wav',
                'eat': 'static/sounds/eat.wav',
                'direction': 'static/sounds/direction.wav',
                'game_over': 'static/sounds/game_over.wav',
                'pause': 'static/sounds/pause.wav',
                'resume': 'static/sounds/resume.wav'
            }
            
            # 加载音效
            self.sound_objects = {}
            self._load_sounds()
            
            # 音效状态
            self.enabled = True
            
            logger.info("音效管理器初始化完成")
        except Exception as e:
            logger.error(f"初始化音效管理器时出错: {str(e)}")
            self.enabled = False
    
    def _load_sounds(self):
        """
        加载所有音效文件
        """
        for name, path in self.sounds.items():
            try:
                # 检查文件是否存在，如果不存在则创建默认音效
                if not os.path.exists(path):
                    self._create_default_sound(name, path)
                
                # 加载音效
                self.sound_objects[name] = pygame.mixer.Sound(path)
                logger.info(f"已加载音效: {name}")
            except Exception as e:
                logger.error(f"加载音效 {name} 时出错: {str(e)}")
    
    def _create_default_sound(self, name, path):
        """
        创建默认音效文件
        
        @param {str} name - 音效名称
        @param {str} path - 音效文件路径
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            # 使用pygame自带的音效文件作为默认音效
            default_sound_path = None
            
            if name == 'start':
                default_sound_path = os.path.join(os.path.dirname(__file__), '../static/sounds/default_start.wav')
            elif name == 'eat':
                default_sound_path = os.path.join(os.path.dirname(__file__), '../static/sounds/default_eat.wav')
            elif name == 'direction':
                default_sound_path = os.path.join(os.path.dirname(__file__), '../static/sounds/default_direction.wav')
            elif name == 'game_over':
                default_sound_path = os.path.join(os.path.dirname(__file__), '../static/sounds/default_game_over.wav')
            elif name == 'pause':
                default_sound_path = os.path.join(os.path.dirname(__file__), '../static/sounds/default_pause.wav')
            elif name == 'resume':
                default_sound_path = os.path.join(os.path.dirname(__file__), '../static/sounds/default_resume.wav')
            
            # 如果默认音效文件不存在，则创建一个空的音效文件
            if default_sound_path and os.path.exists(default_sound_path):
                # 复制默认音效文件
                import shutil
                shutil.copy(default_sound_path, path)
            else:
                # 创建一个空的音效文件
                with open(path, 'wb') as f:
                    # 写入一个最小的WAV文件头
                    f.write(b'RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00')
            
            logger.info(f"已创建默认音效: {name}")
        except Exception as e:
            logger.error(f"创建默认音效 {name} 时出错: {str(e)}")
    
    def play(self, sound_name):
        """
        播放指定音效
        
        @param {str} sound_name - 音效名称
        """
        if not self.enabled:
            return
        
        try:
            if sound_name in self.sound_objects:
                self.sound_objects[sound_name].play()
                logger.debug(f"播放音效: {sound_name}")
            else:
                logger.warning(f"未找到音效: {sound_name}")
        except Exception as e:
            logger.error(f"播放音效 {sound_name} 时出错: {str(e)}")
    
    def toggle(self):
        """
        切换音效开关状态
        
        @returns {bool} 切换后的状态
        """
        self.enabled = not self.enabled
        logger.info(f"音效状态: {'开启' if self.enabled else '关闭'}")
        return self.enabled
    
    def release(self):
        """
        释放资源
        """
        try:
            pygame.mixer.quit()
            logger.info("音效资源已释放")
        except Exception as e:
            logger.error(f"释放音效资源时出错: {str(e)}") 