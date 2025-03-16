import cv2
import logging
import threading
from datetime import datetime
from rich.logging import RichHandler
import os
import time

# 设置日志
if not os.path.exists('logs'):
    os.makedirs('logs')

log_file = f"logs/camera_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        RichHandler(rich_tracebacks=True),
        logging.FileHandler(log_file)
    ]
)
logger = logging.getLogger("camera")

class Camera:
    """
    摄像头处理类，负责捕获视频流
    """
    def __init__(self):
        """
        初始化摄像头
        """
        self.video = None
        self.is_running = False
        self.frame = None
        self.lock = threading.Lock()
        logger.info("摄像头模块初始化完成")
    
    def start(self):
        """
        启动摄像头
        
        @returns {bool} 启动是否成功
        """
        if self.is_running:
            logger.warning("摄像头已经在运行中")
            return True
            
        try:
            # 先确保之前的摄像头已释放
            if self.video is not None:
                self.video.release()
                self.video = None
                time.sleep(0.5)  # 等待资源释放
            
            # 尝试不同的摄像头索引
            for camera_index in range(3):  # 尝试索引0, 1, 2
                logger.info(f"尝试打开摄像头索引 {camera_index}")
                self.video = cv2.VideoCapture(camera_index)
                
                # 设置摄像头属性
                self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                
                # 检查摄像头是否成功打开
                if self.video.isOpened():
                    # 尝试读取一帧，确认摄像头工作正常
                    success, test_frame = self.video.read()
                    if success and test_frame is not None:
                        logger.info(f"成功打开摄像头索引 {camera_index} 并读取测试帧")
                        self.is_running = True
                        threading.Thread(target=self._capture_loop, daemon=True).start()
                        return True
                    else:
                        logger.warning(f"摄像头索引 {camera_index} 打开但无法读取帧")
                        self.video.release()
                else:
                    logger.warning(f"无法打开摄像头索引 {camera_index}")
                    if self.video:
                        self.video.release()
            
            logger.error("所有摄像头索引尝试失败")
            return False
        except Exception as e:
            logger.error(f"摄像头启动失败: {str(e)}")
            if self.video:
                self.video.release()
                self.video = None
            return False
    
    def stop(self):
        """
        停止摄像头
        """
        if not self.is_running:
            logger.info("摄像头已经停止，无需再次停止")
            return
        
        logger.info("正在停止摄像头...")
        self.is_running = False
        
        # 等待一小段时间，确保捕获循环有机会退出
        time.sleep(0.5)
        
        if self.video:
            try:
                self.video.release()
            except Exception as e:
                logger.error(f"释放摄像头资源时出错: {str(e)}")
            finally:
                self.video = None
        
        logger.info("摄像头已停止")
    
    def _capture_loop(self):
        """
        持续捕获视频帧的内部循环
        """
        error_count = 0
        max_errors = 5  # 最大连续错误次数
        
        logger.info("摄像头捕获循环已启动")
        
        while self.is_running:
            try:
                if self.video is None or not self.video.isOpened():
                    logger.error("摄像头已关闭，捕获循环退出")
                    self.is_running = False
                    break
                    
                success, frame = self.video.read()
                if not success:
                    error_count += 1
                    logger.warning(f"无法读取视频帧 (错误 {error_count}/{max_errors})")
                    
                    if error_count >= max_errors:
                        logger.error(f"连续 {max_errors} 次无法读取视频帧，重新初始化摄像头")
                        # 尝试重新初始化摄像头
                        if self.video:
                            self.video.release()
                        
                        self.video = cv2.VideoCapture(0)  # 重新打开摄像头
                        # 设置摄像头属性
                        self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                        self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                        
                        if not self.video.isOpened():
                            logger.error("重新初始化摄像头失败")
                            time.sleep(1)  # 等待一秒再尝试
                        else:
                            logger.info("摄像头重新初始化成功")
                            error_count = 0  # 重置错误计数
                    
                    time.sleep(0.1)  # 短暂等待
                    continue
                    
                # 成功读取，重置错误计数
                error_count = 0
                
                # 水平翻转，使其像镜子一样
                frame = cv2.flip(frame, 1)
                
                with self.lock:
                    self.frame = frame
            except Exception as e:
                logger.error(f"捕获视频帧时出错: {str(e)}")
                time.sleep(0.1)  # 出错时短暂等待
        
        logger.info("摄像头捕获循环已结束")
    
    def get_frame(self):
        """
        获取当前视频帧
        
        @returns {numpy.ndarray|None} 当前视频帧或None
        """
        with self.lock:
            if self.frame is None:
                return None
            return self.frame.copy() 