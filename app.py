from flask import Flask, render_template, Response, jsonify, request
from flask_socketio import SocketIO
import cv2
import base64
import logging
import os
from datetime import datetime
from rich.logging import RichHandler
from dotenv import load_dotenv
from modules.camera import Camera
from modules.gesture import GestureRecognizer
from modules.face import FaceRecognizer
import time
from modules.stats import StatsTracker
from modules.snake_game import SnakeGame
from modules.keyboard_controller import KeyboardController
from modules.gesture_config import GestureConfig
from modules.drawing import DrawingCanvas

# 加载环境变量
load_dotenv()

# 设置日志
if not os.path.exists('logs'):
    os.makedirs('logs')

log_file = f"logs/app_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        RichHandler(rich_tracebacks=True),
        logging.FileHandler(log_file)
    ]
)
logger = logging.getLogger("app")

# 初始化Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'gesture_recognition_secret_key'
socketio = SocketIO(app, 
                   cors_allowed_origins="*", 
                   async_mode='threading',  # 使用线程模式
                   logger=True,  # 启用日志
                   engineio_logger=True)  # 启用Engine.IO日志

# 初始化摄像头、手势识别器、面部识别器和统计跟踪器
camera = Camera()
gesture_recognizer = GestureRecognizer()
face_recognizer = FaceRecognizer()
stats_tracker = StatsTracker()

# 初始化键盘控制器
keyboard_controller = KeyboardController()

# 初始化手势配置
gesture_config = GestureConfig()

# 初始化绘画画布
drawing_canvas = DrawingCanvas()

# 在app.py顶部添加全局变量
face_recognition_enabled = False
keyboard_shortcuts_enabled = False

# 初始化贪吃蛇游戏
snake_game = SnakeGame()

@app.route('/')
def index():
    """渲染主页"""
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    """处理客户端连接"""
    logger.info('客户端已连接')

@socketio.on('disconnect')
def handle_disconnect(data=None):
    """处理客户端断开连接"""
    logger.info('客户端已断开连接')

@socketio.on('start_camera')
def handle_start_camera(data=None):
    """启动摄像头"""
    global camera, gesture_recognizer, face_recognizer  # 确保使用全局变量
    logger.info('尝试启动摄像头')
    
    # 确保之前的摄像头已停止
    camera.stop()
    time.sleep(0.5)  # 等待资源释放
    
    # 重新创建摄像头对象、手势识别器和面部识别器
    camera = Camera()
    gesture_recognizer = GestureRecognizer()
    face_recognizer = FaceRecognizer()
    
    # 尝试启动摄像头，最多尝试3次
    for attempt in range(3):
        logger.info(f'启动摄像头尝试 {attempt+1}/3')
        if camera.start():
            logger.info('摄像头已启动')
            return {'status': 'success'}
        time.sleep(1.0)  # 等待一秒再尝试
    
    logger.error('摄像头启动失败')
    return {'status': 'error', 'message': '无法启动摄像头'}

@socketio.on('stop_camera')
def handle_stop_camera(data=None):
    """停止摄像头"""
    camera.stop()
    logger.info('摄像头已停止')
    return {'status': 'success'}

@socketio.on('toggle_effect')
def handle_toggle_effect(data=None):
    """切换特效"""
    effect_enabled = gesture_recognizer.toggle_matrix_effect()
    logger.info(f'特效状态: {"开启" if effect_enabled else "关闭"}')
    return {'status': 'success', 'enabled': effect_enabled}

@socketio.on('toggle_face_recognition')
def handle_toggle_face_recognition(data=None):
    """切换面部识别"""
    global face_recognition_enabled
    face_recognition_enabled = not face_recognition_enabled
    logger.info(f'面部识别状态: {"开启" if face_recognition_enabled else "关闭"}')
    return {'status': 'success', 'enabled': face_recognition_enabled}

@socketio.on('toggle_keyboard_shortcuts')
def handle_toggle_keyboard_shortcuts(data=None):
    """切换键盘快捷键"""
    global keyboard_shortcuts_enabled
    keyboard_shortcuts_enabled = not keyboard_shortcuts_enabled
    logger.info(f'键盘快捷键状态: {"开启" if keyboard_shortcuts_enabled else "关闭"}')
    return {'status': 'success', 'enabled': keyboard_shortcuts_enabled}

def process_frame():
    """处理视频帧并发送到客户端"""
    logger.info('视频处理线程已启动')
    frame_count = 0
    error_count = 0
    max_errors = 10  # 最大连续错误次数
    
    # 等待摄像头初始化完成
    time.sleep(1.0)
    
    # 确保摄像头已启动
    if not camera.is_running:
        logger.warning('摄像头未运行，尝试启动')
        if not camera.start():
            logger.error('无法启动摄像头，退出视频处理线程')
            socketio.emit('camera_error', {'message': '无法启动摄像头'})
            return
    
    while True:
        try:
            # 检查摄像头是否仍在运行
            if not camera.is_running:
                logger.warning('摄像头已停止运行，尝试重新启动')
                if camera.start():
                    logger.info('摄像头重新启动成功')
                    time.sleep(1.0)  # 等待摄像头初始化
                    continue
                else:
                    logger.error('摄像头重新启动失败，退出视频处理线程')
                    socketio.emit('camera_error', {'message': '摄像头已停止运行且无法重新启动'})
                    break
            
            frame = camera.get_frame()
            if frame is not None:
                try:
                    # 处理帧并识别手势
                    processed_frame, gestures, finger_direction, direction_name = gesture_recognizer.process_frame(frame)
                    
                    # 如果启用了面部识别，处理面部表情
                    expressions = []
                    if face_recognition_enabled and processed_frame is not None:
                        processed_frame, expressions = face_recognizer.process_frame(processed_frame)
                    
                    # 记录统计数据
                    if gestures:
                        stats_tracker.record_gestures(gestures)
                    if expressions:
                        stats_tracker.record_expressions(expressions)
                    
                    # 如果启用了键盘快捷键，处理手势快捷键
                    if keyboard_shortcuts_enabled and gestures:
                        for gesture in gestures:
                            keyboard_controller.handle_gesture(gesture)
                    
                    if processed_frame is not None:
                        # 将帧编码为JPEG
                        _, buffer = cv2.imencode('.jpg', processed_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                        frame_bytes = buffer.tobytes()
                        
                        # 转换为base64字符串
                        frame_base64 = base64.b64encode(frame_bytes).decode('utf-8')
                        
                        # 获取最新统计数据
                        current_stats = stats_tracker.get_stats()
                        
                        # 发送到客户端
                        socketio.emit('frame', {
                            'image': f'data:image/jpeg;base64,{frame_base64}',
                            'gestures': gestures,
                            'expressions': expressions,
                            'stats': current_stats,
                            'direction': direction_name
                        })
                        
                        # 重置错误计数
                        error_count = 0
                        
                        frame_count += 1
                        if frame_count % 100 == 0:  # 每100帧记录一次
                            logger.info(f'已处理 {frame_count} 帧视频')
                            # 每100帧自动保存一次统计数据
                            stats_tracker.save_stats()
                    else:
                        # 如果处理失败但有原始帧，至少发送原始帧
                        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                        frame_bytes = buffer.tobytes()
                        frame_base64 = base64.b64encode(frame_bytes).decode('utf-8')
                        socketio.emit('frame', {
                            'image': f'data:image/jpeg;base64,{frame_base64}',
                            'gestures': [],
                            'expressions': [],
                            'direction': None
                        })
                        
                        logger.warning('处理视频帧失败，发送原始帧')
                        error_count += 1
                except Exception as e:
                    logger.error(f'处理视频帧时出错: {str(e)}')
                    # 如果处理出错但有原始帧，发送原始帧
                    try:
                        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                        frame_bytes = buffer.tobytes()
                        frame_base64 = base64.b64encode(frame_bytes).decode('utf-8')
                        socketio.emit('frame', {
                            'image': f'data:image/jpeg;base64,{frame_base64}',
                            'gestures': [],
                            'expressions': [],
                            'direction': None
                        })
                        logger.warning('发送原始帧')
                    except Exception as frame_error:
                        logger.error(f'发送原始帧时出错: {str(frame_error)}')
                    
                    error_count += 1
            else:
                logger.warning('获取视频帧失败')
                error_count += 1
                
                # 如果连续错误太多，尝试重新启动摄像头
                if error_count == 5:
                    logger.warning('尝试重新启动摄像头')
                    camera.stop()
                    time.sleep(1.0)  # 等待资源释放
                    if camera.start():
                        logger.info('摄像头重新启动成功')
                        error_count = 0  # 重置错误计数
                        time.sleep(1.0)  # 等待摄像头初始化
                        continue
                
                # 如果连续错误太多，可能摄像头已断开
                if error_count > max_errors:
                    logger.error(f'连续 {max_errors} 次获取视频帧失败，停止处理')
                    socketio.emit('camera_error', {'message': '摄像头可能已断开连接'})
                    break
                
                socketio.sleep(0.1)  # 如果获取帧失败，稍微等待长一点
                continue
        except Exception as e:
            logger.error(f'处理视频帧时出错: {str(e)}')
            error_count += 1
            if error_count > max_errors:
                logger.error(f'连续 {max_errors} 次处理错误，停止处理')
                socketio.emit('camera_error', {'message': '视频处理出错'})
                break
            socketio.sleep(0.1)
        
        # 短暂休眠以减少CPU使用率
        socketio.sleep(0.03)  # 约30 FPS

@socketio.on('request_frames')
def handle_request_frames(data=None):
    """处理客户端请求视频帧"""
    logger.info('开始发送视频帧')
    socketio.start_background_task(process_frame)

@socketio.on('get_stats')
def handle_get_stats(data=None):
    """获取统计数据"""
    stats = stats_tracker.get_stats()
    logger.info('发送统计数据')
    return {'status': 'success', 'stats': stats}

@socketio.on('reset_stats')
def handle_reset_stats(data=None):
    """重置统计数据"""
    stats_tracker.reset()
    logger.info('统计数据已重置')
    return {'status': 'success'}

@socketio.on('save_stats')
def handle_save_stats(data=None):
    """保存统计数据"""
    success = stats_tracker.save_stats()
    logger.info('统计数据已保存')
    return {'status': 'success' if success else 'error'}

@app.route('/snake')
def snake():
    """渲染贪吃蛇游戏页面"""
    return render_template('snake.html')

@socketio.on('start_snake_game')
def handle_start_snake_game(data=None):
    """启动贪吃蛇游戏"""
    global snake_game
    logger.info('启动贪吃蛇游戏')
    
    # 重置游戏
    snake_game = SnakeGame()
    
    return {'status': 'success'}

@socketio.on('request_snake_frames')
def handle_request_snake_frames(data=None):
    """处理客户端请求贪吃蛇游戏帧"""
    logger.info('开始发送贪吃蛇游戏帧')
    socketio.start_background_task(process_snake_game)

def process_snake_game():
    """处理贪吃蛇游戏并发送到客户端"""
    logger.info('贪吃蛇游戏线程已启动')
    frame_count = 0
    
    # 确保摄像头已启动
    if not camera.is_running:
        logger.warning('摄像头未运行，尝试启动')
        if not camera.start():
            logger.error('无法启动摄像头，退出贪吃蛇游戏线程')
            socketio.emit('snake_error', {'message': '无法启动摄像头'})
            return
    
    while True:
        try:
            # 获取视频帧
            frame = camera.get_frame()
            if frame is not None:
                # 处理帧并识别手势
                processed_frame, gestures, finger_direction, direction_name = gesture_recognizer.process_frame(frame)
                
                # 记录调试信息
                if finger_direction:
                    logger.debug(f"检测到食指方向: {finger_direction}, 方向名称: {direction_name}")
                
                # 更新游戏状态
                if finger_direction:
                    # 如果检测到方向，无论是否有手势都更新方向
                    snake_game.handle_gesture(gestures[0] if gestures else None, finger_direction)
                elif gestures and len(gestures) > 0:
                    # 如果只有手势没有方向，也传递手势
                    snake_game.handle_gesture(gestures[0], None)
                
                snake_game.update()
                
                # 渲染游戏画面
                game_frame = snake_game.render()
                
                # 将游戏画面编码为JPEG
                _, game_buffer = cv2.imencode('.jpg', game_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                game_bytes = game_buffer.tobytes()
                game_base64 = base64.b64encode(game_bytes).decode('utf-8')
                
                # 将摄像头画面编码为JPEG
                if processed_frame is not None:
                    # 调整摄像头画面大小
                    processed_frame = cv2.resize(processed_frame, (320, 240))
                    _, camera_buffer = cv2.imencode('.jpg', processed_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    camera_bytes = camera_buffer.tobytes()
                    camera_base64 = base64.b64encode(camera_bytes).decode('utf-8')
                else:
                    camera_base64 = None
                
                # 获取游戏信息
                game_info = snake_game.get_game_info()
                
                # 发送到客户端
                socketio.emit('snake_frame', {
                    'game_image': f'data:image/jpeg;base64,{game_base64}',
                    'camera_image': f'data:image/jpeg;base64,{camera_base64}' if camera_base64 else None,
                    'game_info': game_info,
                    'gestures': gestures,
                    'direction': direction_name
                })
                
                frame_count += 1
                if frame_count % 100 == 0:  # 每100帧记录一次
                    logger.info(f'已处理 {frame_count} 帧贪吃蛇游戏')
            else:
                logger.warning('获取视频帧失败')
                socketio.sleep(0.1)
        except Exception as e:
            logger.error(f'处理贪吃蛇游戏帧时出错: {str(e)}')
            socketio.sleep(0.1)
        
        # 按照游戏帧率控制速度
        socketio.sleep(1.0 / snake_game.fps)

@socketio.on('toggle_snake_sound')
def handle_toggle_snake_sound(data=None):
    """切换贪吃蛇游戏音效"""
    enabled = snake_game.sound_manager.toggle()
    logger.info(f'贪吃蛇游戏音效状态: {"开启" if enabled else "关闭"}')
    return {'status': 'success', 'enabled': enabled}

@app.route('/gesture-config')
def gesture_config_page():
    """渲染手势配置页面"""
    return render_template('gesture_config.html')

@app.route('/api/gesture-config', methods=['GET'])
def get_gesture_config():
    """获取手势配置"""
    configs = gesture_config.get_all_configs()
    available_actions = gesture_config.get_available_actions()
    available_shortcuts = gesture_config.get_available_shortcuts()
    
    return jsonify({
        'status': 'success',
        'configs': configs,
        'available_actions': available_actions,
        'available_shortcuts': available_shortcuts
    })

@app.route('/api/gesture-config/<gesture>', methods=['GET'])
def get_specific_gesture_config(gesture):
    """获取特定手势的配置"""
    config = gesture_config.get_gesture_config(gesture)
    
    return jsonify({
        'status': 'success',
        'config': config
    })

@app.route('/api/gesture-config/<gesture>', methods=['POST'])
def update_gesture_config(gesture):
    """更新手势配置"""
    try:
        data = request.json
        action = data.get('action')
        params = data.get('params', {})
        description = data.get('description')
        
        success = gesture_config.set_gesture_config(gesture, action, params, description)
        
        if success:
            # 更新键盘控制器的手势配置
            keyboard_controller.gesture_config = gesture_config
            
            return jsonify({
                'status': 'success',
                'message': f'手势 {gesture} 配置已更新'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'更新手势 {gesture} 配置失败'
            }), 400
    except Exception as e:
        logger.error(f"更新手势配置时出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'更新手势配置时出错: {str(e)}'
        }), 500

@app.route('/api/gesture-config/reset', methods=['POST'])
def reset_gesture_config():
    """重置手势配置为默认值"""
    try:
        success = gesture_config.reset_to_default()
        
        if success:
            # 更新键盘控制器的手势配置
            keyboard_controller.gesture_config = gesture_config
            
            return jsonify({
                'status': 'success',
                'message': '手势配置已重置为默认值'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '重置手势配置失败'
            }), 400
    except Exception as e:
        logger.error(f"重置手势配置时出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'重置手势配置时出错: {str(e)}'
        }), 500

@app.route('/drawing')
def drawing_page():
    """渲染绘画页面"""
    return render_template('drawing.html')

@socketio.on('request_drawing_frames')
def handle_request_drawing_frames(data=None):
    """处理客户端请求绘画帧"""
    logger.info('开始发送绘画帧')
    socketio.start_background_task(process_drawing_frames)

def process_drawing_frames():
    """处理绘画帧并发送到客户端"""
    logger.info('绘画处理线程已启动')
    frame_count = 0
    error_count = 0
    max_errors = 10  # 最大连续错误次数
    
    # 等待摄像头初始化完成
    time.sleep(1.0)
    
    # 确保摄像头已启动
    if not camera.is_running:
        logger.warning('摄像头未运行，尝试启动')
        if not camera.start():
            logger.error('无法启动摄像头，退出绘画处理线程')
            socketio.emit('camera_error', {'message': '无法启动摄像头'})
            return
    
    while True:
        try:
            # 检查摄像头是否仍在运行
            if not camera.is_running:
                logger.warning('摄像头已停止运行，尝试重新启动')
                if camera.start():
                    logger.info('摄像头重新启动成功')
                    time.sleep(1.0)  # 等待摄像头初始化
                    continue
                else:
                    logger.error('摄像头重新启动失败，退出绘画处理线程')
                    socketio.emit('camera_error', {'message': '摄像头已停止运行且无法重新启动'})
                    break
            
            frame = camera.get_frame()
            if frame is not None:
                try:
                    # 处理帧并识别手势
                    processed_frame, hand_landmarks = gesture_recognizer.process_frame_for_drawing(frame)
                    
                    # 处理绘画
                    canvas, is_drawing = drawing_canvas.process_hand_landmarks(
                        hand_landmarks, 
                        frame.shape[1], 
                        frame.shape[0]
                    )
                    
                    # 将画布叠加到视频帧上
                    combined_frame = drawing_canvas.overlay_on_frame(processed_frame)
                    
                    # 将画布编码为JPEG
                    _, canvas_buffer = cv2.imencode('.jpg', canvas, [cv2.IMWRITE_JPEG_QUALITY, 90])
                    canvas_bytes = canvas_buffer.tobytes()
                    canvas_base64 = base64.b64encode(canvas_bytes).decode('utf-8')
                    
                    # 将摄像头画面编码为JPEG
                    _, camera_buffer = cv2.imencode('.jpg', combined_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    camera_bytes = camera_buffer.tobytes()
                    camera_base64 = base64.b64encode(camera_bytes).decode('utf-8')
                    
                    # 发送到客户端
                    socketio.emit('drawing_frame', {
                        'canvas_image': f'data:image/jpeg;base64,{canvas_base64}',
                        'camera_image': f'data:image/jpeg;base64,{camera_base64}',
                        'is_drawing': is_drawing
                    })
                    
                    # 重置错误计数
                    error_count = 0
                    
                    frame_count += 1
                    if frame_count % 100 == 0:  # 每100帧记录一次
                        logger.info(f'已处理 {frame_count} 帧绘画')
                except Exception as e:
                    logger.error(f'处理绘画帧时出错: {str(e)}')
                    error_count += 1
            else:
                logger.warning('获取视频帧失败')
                error_count += 1
                
                # 如果连续错误太多，尝试重新启动摄像头
                if error_count == 5:
                    logger.warning('尝试重新启动摄像头')
                    camera.stop()
                    time.sleep(1.0)  # 等待资源释放
                    if camera.start():
                        logger.info('摄像头重新启动成功')
                        error_count = 0  # 重置错误计数
                        time.sleep(1.0)  # 等待摄像头初始化
                        continue
                
                # 如果连续错误太多，可能摄像头已断开
                if error_count > max_errors:
                    logger.error(f'连续 {max_errors} 次获取视频帧失败，停止处理')
                    socketio.emit('camera_error', {'message': '摄像头可能已断开连接'})
                    break
                
                socketio.sleep(0.1)  # 如果获取帧失败，稍微等待长一点
                continue
        except Exception as e:
            logger.error(f'处理绘画帧时出错: {str(e)}')
            error_count += 1
            if error_count > max_errors:
                logger.error(f'连续 {max_errors} 次处理错误，停止处理')
                socketio.emit('camera_error', {'message': '绘画处理出错'})
                break
            socketio.sleep(0.1)
        
        # 短暂休眠以减少CPU使用率
        socketio.sleep(0.03)  # 约30 FPS

@socketio.on('toggle_eraser')
def handle_toggle_eraser(data=None):
    """切换橡皮擦模式"""
    enabled = drawing_canvas.toggle_eraser()
    logger.info(f'橡皮擦模式: {"开启" if enabled else "关闭"}')
    return {'status': 'success', 'enabled': enabled}

@socketio.on('clear_canvas')
def handle_clear_canvas(data=None):
    """清空画布"""
    drawing_canvas.clear()
    logger.info('画布已清空')
    return {'status': 'success'}

@socketio.on('undo_drawing')
def handle_undo_drawing(data=None):
    """撤销绘画"""
    success = drawing_canvas.undo()
    logger.info('撤销绘画操作')
    return {'status': 'success' if success else 'error'}

@socketio.on('save_drawing')
def handle_save_drawing(data=None):
    """保存绘画"""
    filepath = drawing_canvas.save_canvas()
    logger.info(f'绘画已保存到: {filepath}')
    return {'status': 'success', 'filepath': filepath}

@socketio.on('set_color')
def handle_set_color(data):
    """设置绘画颜色"""
    r = data.get('r', 0)
    g = data.get('g', 0)
    b = data.get('b', 0)
    drawing_canvas.set_color((b, g, r))  # OpenCV使用BGR顺序
    logger.info(f'设置绘画颜色: ({r}, {g}, {b})')
    return {'status': 'success'}

@socketio.on('set_brush_size')
def handle_set_brush_size(data):
    """设置画笔大小"""
    size = data.get('size', 5)
    drawing_canvas.set_brush_size(size)
    logger.info(f'设置画笔大小: {size}')
    return {'status': 'success'}

@socketio.on('set_eraser_size')
def handle_set_eraser_size(data):
    """设置橡皮擦大小"""
    size = data.get('size', 20)
    drawing_canvas.set_eraser_size(size)
    logger.info(f'设置橡皮擦大小: {size}')
    return {'status': 'success'}

@socketio.on('set_drawing_finger')
def handle_set_drawing_finger(data):
    """设置绘画手指"""
    finger = data.get('finger', 'index')
    success = drawing_canvas.set_drawing_finger(finger)
    logger.info(f'设置绘画手指: {finger}')
    return {'status': 'success' if success else 'error'}

@app.errorhandler(Exception)
def handle_error(e):
    """全局错误处理"""
    logger.error(f"应用错误: {str(e)}")
    return jsonify({"error": str(e)}), 500

@app.teardown_appcontext
def cleanup(exception=None):
    """应用上下文结束时清理资源"""
    # 只在应用完全关闭时才释放资源
    # 不要在每个请求结束时都释放资源
    if exception is not None:
        logger.info(f"应用上下文结束，异常: {str(exception)}")
        # 保存统计数据
        stats_tracker.save_stats()
        # 释放资源
        camera.stop()
        gesture_recognizer.release()
        face_recognizer.release()

if __name__ == '__main__':
    logger.info("手势识别Web应用启动")
    socketio.run(app, host='0.0.0.0', port=8080, debug=True, allow_unsafe_werkzeug=True) 