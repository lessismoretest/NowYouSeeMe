import cv2
import mediapipe as mp
import numpy as np
import logging
from datetime import datetime
from rich.logging import RichHandler
import os
from collections import deque

# 设置日志
if not os.path.exists('logs'):
    os.makedirs('logs')

log_file = f"logs/face_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        RichHandler(rich_tracebacks=True),
        logging.FileHandler(log_file)
    ]
)
logger = logging.getLogger("face")

class FaceRecognizer:
    """
    面部识别类，负责识别面部表情如微笑和眨眼
    """
    def __init__(self):
        """
        初始化面部识别器
        """
        try:
            # 初始化MediaPipe Face Mesh
            self.mp_face_mesh = mp.solutions.face_mesh
            self.mp_drawing = mp.solutions.drawing_utils
            self.drawing_spec = self.mp_drawing.DrawingSpec(thickness=1, circle_radius=1)
            
            # 初始化面部网格检测器
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=1,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            
            # 定义面部表情
            self.expressions = {
                "smile": "微笑",
                "blink": "眨眼",
                "neutral": "正常"
            }
            
            # 定义关键点索引
            # 嘴巴关键点 - 更精确的嘴角和嘴唇点
            self.mouth_top = [13, 14, 312]  # 上嘴唇中心点
            self.mouth_bottom = [14, 17, 317]  # 下嘴唇中心点
            self.mouth_left = [61, 291]  # 左嘴角
            self.mouth_right = [291, 402]  # 右嘴角
            
            # 左眼关键点 - 更精确的眼睛轮廓点
            self.left_eye_top = [386, 374, 159, 145]  # 左眼上缘
            self.left_eye_bottom = [380, 385, 384, 398]  # 左眼下缘
            self.left_eye_left = [362]  # 左眼左角
            self.left_eye_right = [263]  # 左眼右角
            
            # 右眼关键点
            self.right_eye_top = [159, 145, 158, 153]  # 右眼上缘
            self.right_eye_bottom = [145, 153, 133, 173]  # 右眼下缘
            self.right_eye_left = [133]  # 右眼左角
            self.right_eye_right = [33]  # 右眼右角
            
            # 状态变量
            self.left_eye_state = deque(maxlen=10)  # 存储最近10帧左眼状态
            self.right_eye_state = deque(maxlen=10)  # 存储最近10帧右眼状态
            self.smile_state = deque(maxlen=10)  # 存储最近10帧微笑状态
            
            # 表情检测阈值
            self.eye_aspect_ratio_threshold = 0.2  # 眼睛长宽比阈值，小于此值认为眼睛闭合
            self.smile_ratio_threshold = 3.5  # 嘴巴宽高比阈值，大于此值认为在微笑
            
            # 连续帧阈值
            self.blink_frames_threshold = 3  # 连续多少帧检测到眨眼才算一次眨眼
            self.smile_frames_threshold = 5  # 连续多少帧检测到微笑才算一次微笑
            
            # 冷却时间（避免重复检测）
            self.blink_cooldown = 0
            self.smile_cooldown = 0
            self.cooldown_frames = 15  # 冷却帧数
            
            # 调试模式
            self.debug = True
            
            logger.info("面部识别模块初始化完成")
        except Exception as e:
            logger.error(f"初始化面部识别器时出错: {str(e)}")
            # 确保即使初始化失败，对象也能正常使用
            if not hasattr(self, 'mp_face_mesh'):
                self.mp_face_mesh = mp.solutions.face_mesh
            if not hasattr(self, 'mp_drawing'):
                self.mp_drawing = mp.solutions.drawing_utils
            if not hasattr(self, 'face_mesh'):
                self.face_mesh = None
    
    def process_frame(self, frame):
        """
        处理视频帧，检测面部表情
        
        @param {numpy.ndarray} frame - 输入的视频帧
        @returns {tuple} (处理后的帧, 识别到的表情)
        """
        if frame is None:
            return None, []
        
        try:
            # 检查面部识别器是否已初始化
            if not hasattr(self, 'face_mesh') or self.face_mesh is None:
                logger.warning("面部识别器未初始化，重新初始化")
                self.face_mesh = self.mp_face_mesh.FaceMesh(
                    static_image_mode=False,
                    max_num_faces=1,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
            
            # 转换为RGB格式
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # 处理图像
            results = self.face_mesh.process(rgb_frame)
            
            # 复制原始帧用于绘制
            annotated_frame = frame.copy()
            
            detected_expressions = []
            
            # 更新冷却计数器
            if self.blink_cooldown > 0:
                self.blink_cooldown -= 1
            if self.smile_cooldown > 0:
                self.smile_cooldown -= 1
            
            # 如果检测到面部
            if results.multi_face_landmarks:
                for face_landmarks in results.multi_face_landmarks:
                    # 绘制面部网格
                    self.mp_drawing.draw_landmarks(
                        image=annotated_frame,
                        landmark_list=face_landmarks,
                        connections=self.mp_face_mesh.FACEMESH_TESSELATION,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=1)
                    )
                    
                    # 提取关键点坐标
                    h, w, _ = annotated_frame.shape
                    landmarks = []
                    for landmark in face_landmarks.landmark:
                        x, y = int(landmark.x * w), int(landmark.y * h)
                        landmarks.append((x, y))
                    landmarks = np.array(landmarks)
                    
                    # 检测眨眼
                    left_eye_closed = self._is_eye_closed(landmarks, self.left_eye_top, self.left_eye_bottom, self.left_eye_left, self.left_eye_right)
                    right_eye_closed = self._is_eye_closed(landmarks, self.right_eye_top, self.right_eye_bottom, self.right_eye_left, self.right_eye_right)
                    
                    # 更新眼睛状态队列
                    self.left_eye_state.append(left_eye_closed)
                    self.right_eye_state.append(right_eye_closed)
                    
                    # 检测微笑
                    is_smiling = self._is_smiling(landmarks)
                    
                    # 更新微笑状态队列
                    self.smile_state.append(is_smiling)
                    
                    # 在调试模式下显示眼睛和嘴巴状态
                    if self.debug:
                        left_status = "闭合" if left_eye_closed else "睁开"
                        right_status = "闭合" if right_eye_closed else "睁开"
                        smile_status = "微笑" if is_smiling else "不笑"
                        
                        cv2.putText(annotated_frame, f"左眼: {left_status}", (10, 30), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        cv2.putText(annotated_frame, f"右眼: {right_status}", (10, 60), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        cv2.putText(annotated_frame, f"嘴巴: {smile_status}", (10, 90), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    
                    # 判断是否眨眼（两只眼睛都闭合然后睁开）
                    if self.blink_cooldown == 0 and self._detect_blink():
                        detected_expressions.append("blink")
                        self.blink_cooldown = self.cooldown_frames
                        logger.info("检测到眨眼")
                    
                    # 判断是否微笑
                    if self.smile_cooldown == 0 and self._detect_smile():
                        detected_expressions.append("smile")
                        self.smile_cooldown = self.cooldown_frames
                        logger.info("检测到微笑")
            
            return annotated_frame, detected_expressions
            
        except Exception as e:
            logger.error(f"处理视频帧时出错: {str(e)}")
            # 如果出错，尝试重新初始化面部识别器
            try:
                if hasattr(self, 'face_mesh') and self.face_mesh is not None:
                    self.face_mesh.close()
                self.face_mesh = self.mp_face_mesh.FaceMesh(
                    static_image_mode=False,
                    max_num_faces=1,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
                logger.info("面部识别器已重新初始化")
            except Exception as reinit_error:
                logger.error(f"重新初始化面部识别器失败: {str(reinit_error)}")
            
            # 返回原始帧和空表情列表
            return frame, []
    
    def _is_eye_closed(self, landmarks, top_points, bottom_points, left_point, right_point):
        """
        判断眼睛是否闭合
        
        @param {numpy.ndarray} landmarks - 面部关键点
        @param {list} top_points - 眼睛上缘点索引
        @param {list} bottom_points - 眼睛下缘点索引
        @param {list} left_point - 眼睛左角点索引
        @param {list} right_point - 眼睛右角点索引
        @returns {bool} 眼睛是否闭合
        """
        # 计算眼睛的高度（上下缘的平均距离）
        eye_height = 0
        for top_idx in top_points:
            for bottom_idx in bottom_points:
                height = np.linalg.norm(landmarks[top_idx] - landmarks[bottom_idx])
                eye_height += height
        eye_height /= (len(top_points) * len(bottom_points))
        
        # 计算眼睛的宽度
        eye_width = np.linalg.norm(landmarks[left_point[0]] - landmarks[right_point[0]])
        
        # 计算眼睛长宽比
        ear = eye_height / eye_width if eye_width > 0 else 1.0
        
        # 判断眼睛是否闭合
        return ear < self.eye_aspect_ratio_threshold
    
    def _is_smiling(self, landmarks):
        """
        判断是否在微笑
        
        @param {numpy.ndarray} landmarks - 面部关键点
        @returns {bool} 是否在微笑
        """
        # 计算嘴巴的宽度（左右嘴角的距离）
        mouth_width = np.linalg.norm(landmarks[self.mouth_left[0]] - landmarks[self.mouth_right[0]])
        
        # 计算嘴巴的高度（上下嘴唇的距离）
        mouth_height = np.linalg.norm(landmarks[self.mouth_top[0]] - landmarks[self.mouth_bottom[0]])
        
        # 计算嘴巴宽高比
        mar = mouth_width / mouth_height if mouth_height > 0 else 0
        
        # 判断是否在微笑
        return mar > self.smile_ratio_threshold
    
    def _detect_blink(self):
        """
        检测眨眼动作（闭眼然后睁眼的过程）
        
        @returns {bool} 是否检测到眨眼
        """
        if len(self.left_eye_state) < self.blink_frames_threshold or len(self.right_eye_state) < self.blink_frames_threshold:
            return False
        
        # 检查是否有连续的闭眼帧，然后是睁眼帧
        left_closed_count = sum(1 for state in list(self.left_eye_state)[-self.blink_frames_threshold:] if state)
        right_closed_count = sum(1 for state in list(self.right_eye_state)[-self.blink_frames_threshold:] if state)
        
        # 最近的帧是否是睁眼状态
        recent_left_open = not self.left_eye_state[-1]
        recent_right_open = not self.right_eye_state[-1]
        
        # 之前是否有足够的闭眼帧
        enough_left_closed = left_closed_count >= self.blink_frames_threshold - 1
        enough_right_closed = right_closed_count >= self.blink_frames_threshold - 1
        
        # 检测到眨眼的条件：之前有足够的闭眼帧，最近的帧是睁眼状态
        return (enough_left_closed and recent_left_open) or (enough_right_closed and recent_right_open)
    
    def _detect_smile(self):
        """
        检测微笑动作
        
        @returns {bool} 是否检测到微笑
        """
        if len(self.smile_state) < self.smile_frames_threshold:
            return False
        
        # 检查是否有连续的微笑帧
        smile_count = sum(1 for state in list(self.smile_state)[-self.smile_frames_threshold:] if state)
        
        # 如果连续帧中大部分是微笑状态，则认为检测到微笑
        return smile_count >= self.smile_frames_threshold - 1
    
    def release(self):
        """
        释放资源
        """
        try:
            if hasattr(self, 'face_mesh') and self.face_mesh is not None:
                self.face_mesh.close()
        except Exception as e:
            logger.error(f"释放面部识别资源时出错: {str(e)}")
        logger.info("面部识别资源已释放") 