# 手势识别互动系统 (Now You See Me)

一个基于计算机视觉的手势识别互动系统，支持手势识别、面部表情识别以及手势控制贪吃蛇游戏。

## 功能特性

- **实时手势识别**：识别多种手势，如握拳、张开手掌、指向等
- **面部表情识别**：检测微笑和眨眼等面部表情
- **特效模式**：支持"黑客帝国"风格的视觉特效
- **贪吃蛇游戏**：使用食指方向控制贪吃蛇移动
- **统计分析**：记录和分析手势和表情的使用频率
- **音效系统**：游戏中的各种动作配有音效

## 系统架构

```mermaid
graph TD
    A[客户端浏览器] <-->|WebSocket| B[Flask服务器]
    B --> C[摄像头模块]
    B --> D[手势识别模块]
    B --> E[面部识别模块]
    B --> F[贪吃蛇游戏模块]
    B --> G[统计模块]
    F --> H[音效管理模块]
    
    C -->|视频帧| D
    C -->|视频帧| E
    D -->|手势数据| B
    E -->|表情数据| B
    D -->|方向控制| F
    F -->|游戏状态| B
    G -->|统计数据| B
```

## 模块说明

- **Camera**: 摄像头模块，负责捕获视频流
- **GestureRecognizer**: 手势识别模块，使用MediaPipe进行手部检测和手势识别
- **FaceRecognizer**: 面部识别模块，负责识别面部表情如微笑和眨眼
- **SnakeGame**: 贪吃蛇游戏模块，使用食指控制蛇的移动方向
- **StatsTracker**: 统计模块，记录和分析手势和表情的使用频率
- **SoundManager**: 音效管理模块，负责加载和播放游戏音效

## 技术栈

- **后端**: Flask, Flask-SocketIO
- **计算机视觉**: OpenCV, MediaPipe
- **前端**: HTML, CSS, JavaScript, Socket.IO
- **游戏引擎**: Pygame (后端渲染)
- **日志系统**: Rich (美化终端输出)

## 安装说明

### 环境要求

- Python 3.8+
- 摄像头设备

### 安装步骤

1. 克隆仓库
   ```bash
   git clone https://github.com/yourusername/NowYouSeeMe.git
   cd NowYouSeeMe
   ```

2. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

3. 创建默认音效文件（如果需要）
   ```bash
   python create_default_sounds.py
   ```

4. 启动应用
   ```bash
   python app.py
   ```

5. 在浏览器中访问
   ```
   http://localhost:8080
   ```

## 使用方法

### 主界面

1. 点击"启动摄像头"按钮开始视频流
2. 使用"开启黑客帝国特效"按钮切换视觉特效
3. 使用"开启面部识别"按钮启用面部表情识别
4. 点击"贪吃蛇游戏"进入游戏模式

### 贪吃蛇游戏

1. 使用食指指向不同方向控制蛇的移动
2. 手势"握拳"可以暂停/继续游戏
3. 手势"OK"可以重新开始游戏
4. 点击"开启/关闭音效"按钮控制游戏音效

## 支持的手势

- 握拳
- 张开手掌
- OK手势
- 指向（上、下、左、右）
- 更多手势...

## 支持的面部表情

- 微笑
- 眨眼
- 更多表情...

## 日志系统

系统自动在`logs`目录下生成日志文件，按模块和日期分类：
- `app_YYYYMMDD.log`
- `camera_YYYYMMDD.log`
- `gesture_YYYYMMDD.log`
- `face_YYYYMMDD.log`
- `snake_game_YYYYMMDD.log`
- `stats_YYYYMMDD.log`
- `sound_YYYYMMDD.log`

## 统计数据

系统会自动记录手势和表情的使用频率，并在`stats`目录下保存统计数据。

## 许可证

MIT

## 贡献指南

欢迎提交问题和拉取请求！

## 致谢

- MediaPipe团队提供的出色的计算机视觉库
- Flask和Socket.IO团队提供的实时通信框架 