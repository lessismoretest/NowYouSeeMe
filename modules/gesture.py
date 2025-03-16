import cv2
import mediapipe as mp
import numpy as np
import logging
import random
from datetime import datetime
from rich.logging import RichHandler
import os

# 设置日志
if not os.path.exists('logs'):
    os.makedirs('logs')

log_file = f"logs/gesture_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        RichHandler(rich_tracebacks=True),
        logging.FileHandler(log_file)
    ]
)
logger = logging.getLogger("gesture")

class GestureRecognizer:
    """
    手势识别类，使用MediaPipe进行手部检测和手势识别
    """
    def __init__(self):
        """
        初始化手势识别器
        """
        try:
            self.mp_hands = mp.solutions.hands
            self.mp_drawing = mp.solutions.drawing_utils
            self.mp_drawing_styles = mp.solutions.drawing_styles
            
            # 初始化手部检测器
            self.hands = self.mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=2,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            
            # 手势定义
            self.gestures = {
                "fist": "握拳",
                "palm": "手掌",
                "thumb_up": "点赞",
                "peace": "剪刀手",
                "pointing": "指向",
                "zoom_in": "放大",
                "zoom_out": "缩小"
            }
            
            # 特效相关
            self.matrix_effect_enabled = False
            self.matrix_chars = []
            self.init_matrix_effect()
            
            # 双手手势相关
            self.prev_hands_distance = None
            self.distance_threshold = 0.05  # 距离变化阈值
            self.zoom_cooldown = 0
            self.zoom_cooldown_frames = 10  # 缩放手势冷却帧数
            
            logger.info("手势识别模块初始化完成")
        except Exception as e:
            logger.error(f"初始化手势识别器时出错: {str(e)}")
            # 确保即使初始化失败，对象也能正常使用
            if not hasattr(self, 'mp_hands'):
                self.mp_hands = mp.solutions.hands
            if not hasattr(self, 'mp_drawing'):
                self.mp_drawing = mp.solutions.drawing_utils
            if not hasattr(self, 'mp_drawing_styles'):
                self.mp_drawing_styles = mp.solutions.drawing_styles
            if not hasattr(self, 'hands'):
                self.hands = None
            if not hasattr(self, 'gestures'):
                self.gestures = {}
            if not hasattr(self, 'matrix_effect_enabled'):
                self.matrix_effect_enabled = False
            if not hasattr(self, 'matrix_chars'):
                self.matrix_chars = []
    
    def init_matrix_effect(self):
        """初始化黑客帝国特效"""
        # 创建一些随机的字符用于矩阵效果
        chars = "01"
        self.matrix_chars = []
        for i in range(100):  # 创建100个随机字符
            char = random.choice(chars)
            x = random.randint(0, 640)
            y = random.randint(0, 480)
            speed = random.randint(5, 15)
            size = random.uniform(0.5, 1.5)
            self.matrix_chars.append({
                'char': char,
                'x': x,
                'y': y,
                'speed': speed,
                'size': size
            })
    
    def toggle_matrix_effect(self):
        """切换黑客帝国特效状态"""
        self.matrix_effect_enabled = not self.matrix_effect_enabled
        logger.info(f"黑客帝国特效: {'开启' if self.matrix_effect_enabled else '关闭'}")
        return self.matrix_effect_enabled
    
    def apply_matrix_effect(self, image):
        """应用黑客帝国特效"""
        if not self.matrix_effect_enabled:
            return image
        
        # 创建一个黑色背景
        height, width = image.shape[:2]
        matrix_overlay = np.zeros((height, width, 3), dtype=np.uint8)
        
        # 更新字符位置并绘制
        for char in self.matrix_chars:
            # 更新Y位置（下落效果）
            char['y'] += char['speed']
            if char['y'] > height:
                char['y'] = 0
                char['x'] = random.randint(0, width)
            
            # 绘制字符
            font = cv2.FONT_HERSHEY_SIMPLEX
            color = (0, 255, 0)  # 绿色
            cv2.putText(matrix_overlay, char['char'], 
                       (int(char['x']), int(char['y'])), 
                       font, char['size'], color, 1, cv2.LINE_AA)
        
        # 将原始图像转换为绿色色调
        green_image = np.zeros_like(image)
        green_image[:,:,1] = image[:,:,1]  # 只保留绿色通道
        
        # 混合原始图像和矩阵效果
        alpha = 0.7
        beta = 0.5
        gamma = 0
        
        # 先将原始图像转为绿色调
        green_tint = cv2.addWeighted(image, 0.1, green_image, 0.9, gamma)
        
        # 然后添加矩阵字符
        result = cv2.addWeighted(green_tint, alpha, matrix_overlay, beta, gamma)
        
        return result
    
    def process_frame(self, frame):
        """
        处理视频帧，检测手部并识别手势
        
        @param {numpy.ndarray} frame - 输入的视频帧
        @returns {tuple} (处理后的帧, 识别到的手势, 食指方向, 方向名称)
        """
        if frame is None:
            return None, [], None, None
        
        try:
            # 检查手势识别器是否已初始化
            if not hasattr(self, 'hands') or self.hands is None:
                logger.warning("手势识别器未初始化，重新初始化")
                self.hands = self.mp_hands.Hands(
                    static_image_mode=False,
                    max_num_hands=2,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
            
            # 转换为RGB格式，MediaPipe需要RGB输入
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # 处理图像
            results = self.hands.process(rgb_frame)
            
            # 复制原始帧用于绘制
            annotated_frame = frame.copy()
            
            detected_gestures = []
            finger_direction = None
            direction_name = None
            
            # 缩放手势冷却时间减少
            if hasattr(self, 'zoom_cooldown') and self.zoom_cooldown > 0:
                self.zoom_cooldown -= 1
            
            # 如果检测到手
            if results.multi_hand_landmarks:
                # 检测到的手的数量
                num_hands = len(results.multi_hand_landmarks)
                
                # 如果检测到两只手，处理双手手势
                if num_hands == 2:
                    # 获取两只手的中心点
                    hand1_landmarks = results.multi_hand_landmarks[0].landmark
                    hand2_landmarks = results.multi_hand_landmarks[1].landmark
                    
                    # 计算两手中心点
                    hand1_center_x = sum(landmark.x for landmark in hand1_landmarks) / len(hand1_landmarks)
                    hand1_center_y = sum(landmark.y for landmark in hand1_landmarks) / len(hand1_landmarks)
                    
                    hand2_center_x = sum(landmark.x for landmark in hand2_landmarks) / len(hand2_landmarks)
                    hand2_center_y = sum(landmark.y for landmark in hand2_landmarks) / len(hand2_landmarks)
                    
                    # 计算两手之间的距离
                    current_distance = np.sqrt((hand1_center_x - hand2_center_x)**2 + (hand1_center_y - hand2_center_y)**2)
                    
                    # 在图像上绘制两手之间的连线
                    h, w, c = annotated_frame.shape
                    hand1_center = (int(hand1_center_x * w), int(hand1_center_y * h))
                    hand2_center = (int(hand2_center_x * w), int(hand2_center_y * h))
                    cv2.line(annotated_frame, hand1_center, hand2_center, (255, 0, 255), 2)
                    
                    # 在连线中间显示距离
                    mid_point = ((hand1_center[0] + hand2_center[0]) // 2, (hand1_center[1] + hand2_center[1]) // 2)
                    cv2.putText(
                        annotated_frame,
                        f"距离: {current_distance:.2f}",
                        mid_point,
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (255, 0, 255),
                        2
                    )
                    
                    # 如果有前一帧的距离记录，比较距离变化
                    if hasattr(self, 'prev_hands_distance') and self.prev_hands_distance is not None and self.zoom_cooldown == 0:
                        # 计算距离变化
                        distance_change = current_distance - self.prev_hands_distance
                        
                        # 如果距离变化超过阈值，识别为缩放手势
                        if abs(distance_change) > self.distance_threshold:
                            if distance_change > 0:
                                # 两手分开，放大
                                detected_gestures.append("zoom_in")
                                logger.info(f"检测到放大手势，距离变化: {distance_change:.2f}")
                            else:
                                # 两手靠近，缩小
                                detected_gestures.append("zoom_out")
                                logger.info(f"检测到缩小手势，距离变化: {distance_change:.2f}")
                            
                            # 设置缩放手势冷却时间
                            self.zoom_cooldown = self.zoom_cooldown_frames
                    
                    # 更新前一帧的距离记录
                    self.prev_hands_distance = current_distance
                else:
                    # 如果只检测到一只手，重置前一帧的距离记录
                    self.prev_hands_distance = None
                
                # 处理每只手的单手手势
                for hand_landmarks in results.multi_hand_landmarks:
                    # 绘制手部关键点和连接线
                    self.mp_drawing.draw_landmarks(
                        annotated_frame,
                        hand_landmarks,
                        self.mp_hands.HAND_CONNECTIONS,
                        self.mp_drawing_styles.get_default_hand_landmarks_style(),
                        self.mp_drawing_styles.get_default_hand_connections_style()
                    )
                    
                    # 识别手势
                    gesture = self._recognize_gesture(hand_landmarks.landmark)
                    
                    # 无论是什么手势，都计算食指方向
                    # 这样即使手势不是"指向"，也能获取食指方向
                    finger_direction, direction_name = self._get_finger_direction(hand_landmarks.landmark)
                    
                    # 在图像上绘制方向箭头
                    h, w, c = annotated_frame.shape
                    landmarks = hand_landmarks.landmark
                    index_mcp = landmarks[self.mp_hands.HandLandmark.INDEX_FINGER_MCP.value]
                    index_tip = landmarks[self.mp_hands.HandLandmark.INDEX_FINGER_TIP.value]
                    
                    # 计算箭头起点和终点
                    start_point = (int(index_mcp.x * w), int(index_mcp.y * h))
                    end_point = (int(index_tip.x * w), int(index_tip.y * h))
                    
                    # 绘制箭头
                    cv2.arrowedLine(
                        annotated_frame, 
                        start_point, 
                        end_point, 
                        (0, 255, 255), 
                        2, 
                        tipLength=0.3
                    )
                    
                    # 在箭头附近显示方向名称
                    cv2.putText(
                        annotated_frame,
                        f"方向: {direction_name}",
                        (end_point[0] + 10, end_point[1]),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 255),
                        2
                    )
                    
                    if gesture and gesture not in ["zoom_in", "zoom_out"]:
                        # 避免重复添加缩放手势
                        if gesture not in detected_gestures:
                            detected_gestures.append(gesture)
                        
                        # 在图像上显示手势名称
                        cx = int(sum(landmark.x for landmark in landmarks) / len(landmarks) * w)
                        cy = int(sum(landmark.y for landmark in landmarks) / len(landmarks) * h)
                        
                        # 在图像上显示手势名称
                        cv2.putText(
                            annotated_frame, 
                            self.gestures.get(gesture, gesture), 
                            (cx - 50, cy - 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 
                            1, 
                            (0, 255, 0), 
                            2
                        )
            
            # 应用黑客帝国特效（如果启用）
            if self.matrix_effect_enabled:
                annotated_frame = self.apply_matrix_effect(annotated_frame)
            
            return annotated_frame, detected_gestures, finger_direction, direction_name
            
        except Exception as e:
            logger.error(f"处理视频帧时出错: {str(e)}")
            # 如果出错，尝试重新初始化手势识别器
            try:
                if hasattr(self, 'hands') and self.hands is not None:
                    self.hands.close()
                self.hands = self.mp_hands.Hands(
                    static_image_mode=False,
                    max_num_hands=2,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
                logger.info("手势识别器已重新初始化")
            except Exception as reinit_error:
                logger.error(f"重新初始化手势识别器失败: {str(reinit_error)}")
            
            # 返回原始帧和空手势列表
            return frame, [], None, None
    
    def _recognize_gesture(self, landmarks):
        """
        识别手势
        
        @param {list} landmarks - 手部关键点
        @returns {str} 识别到的手势名称
        """
        if not landmarks:
            return None
        
        # 获取特定关键点
        thumb_tip = landmarks[self.mp_hands.HandLandmark.THUMB_TIP.value]
        thumb_ip = landmarks[self.mp_hands.HandLandmark.THUMB_IP.value]
        index_tip = landmarks[self.mp_hands.HandLandmark.INDEX_FINGER_TIP.value]
        index_pip = landmarks[self.mp_hands.HandLandmark.INDEX_FINGER_PIP.value]
        middle_tip = landmarks[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP.value]
        middle_pip = landmarks[self.mp_hands.HandLandmark.MIDDLE_FINGER_PIP.value]
        ring_tip = landmarks[self.mp_hands.HandLandmark.RING_FINGER_TIP.value]
        ring_pip = landmarks[self.mp_hands.HandLandmark.RING_FINGER_PIP.value]
        pinky_tip = landmarks[self.mp_hands.HandLandmark.PINKY_TIP.value]
        pinky_pip = landmarks[self.mp_hands.HandLandmark.PINKY_PIP.value]
        
        # 计算手指是否伸展
        thumb_extended = thumb_tip.y < thumb_ip.y  # Y坐标比较
        index_extended = index_tip.y < index_pip.y
        middle_extended = middle_tip.y < middle_pip.y
        ring_extended = ring_tip.y < ring_pip.y
        pinky_extended = pinky_tip.y < pinky_pip.y
        
        # 识别手势
        # 握拳：所有手指都弯曲
        if not any([thumb_extended, index_extended, middle_extended, ring_extended, pinky_extended]):
            return "fist"
        
        # 手掌：所有手指都伸展
        if all([thumb_extended, index_extended, middle_extended, ring_extended, pinky_extended]):
            return "palm"
        
        # 点赞：只有拇指伸展
        if thumb_extended and not any([index_extended, middle_extended, ring_extended, pinky_extended]):
            return "thumb_up"
        
        # 剪刀手：食指和中指伸展，其他弯曲
        if index_extended and middle_extended and not any([thumb_extended, ring_extended, pinky_extended]):
            return "peace"
        
        # 指向：只有食指伸展
        if index_extended and not any([thumb_extended, middle_extended, ring_extended, pinky_extended]):
            return "pointing"
        
        # 无法识别的手势
        return None
    
    def _get_finger_direction(self, landmarks):
        """
        计算食指的指向方向
        
        @param {list} landmarks - 手部关键点
        @returns {tuple} 食指方向向量 (x, y) 和方向名称
        """
        try:
            # 获取食指关键点
            wrist = landmarks[self.mp_hands.HandLandmark.WRIST.value]
            index_mcp = landmarks[self.mp_hands.HandLandmark.INDEX_FINGER_MCP.value]
            index_pip = landmarks[self.mp_hands.HandLandmark.INDEX_FINGER_PIP.value]
            index_tip = landmarks[self.mp_hands.HandLandmark.INDEX_FINGER_TIP.value]
            
            # 使用整个食指的方向，而不仅仅是指尖和指根
            # 这样可以获得更稳定的方向
            dx = index_tip.x - index_mcp.x
            dy = index_tip.y - index_mcp.y
            
            # 归一化向量
            length = np.sqrt(dx**2 + dy**2)
            if length > 0:
                dx /= length
                dy /= length
            
            # 确定方向名称
            direction_name = "未知"
            
            # 使用更宽松的阈值，更容易识别主要方向
            if abs(dx) > abs(dy) * 1.2:  # 水平方向为主
                direction_name = "右" if dx > 0 else "左"
            elif abs(dy) > abs(dx) * 1.2:  # 垂直方向为主
                direction_name = "下" if dy > 0 else "上"
            else:  # 对角线方向
                if dx > 0 and dy < 0:
                    direction_name = "右上"
                elif dx > 0 and dy > 0:
                    direction_name = "右下"
                elif dx < 0 and dy < 0:
                    direction_name = "左上"
                elif dx < 0 and dy > 0:
                    direction_name = "左下"
            
            logger.debug(f"食指方向: dx={dx:.2f}, dy={dy:.2f}, 方向={direction_name}")
            return (dx, dy), direction_name
        except Exception as e:
            logger.error(f"计算食指方向时出错: {str(e)}")
            return None, "错误"
    
    def release(self):
        """
        释放资源
        """
        try:
            if hasattr(self, 'hands') and self.hands is not None:
                self.hands.close()
        except Exception as e:
            logger.error(f"释放手势识别资源时出错: {str(e)}")
        logger.info("手势识别资源已释放") 