document.addEventListener('DOMContentLoaded', function() {
    // 获取DOM元素
    const videoFeed = document.getElementById('video-feed');
    const loadingIndicator = document.getElementById('loading-indicator');
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    const gestureResult = document.getElementById('gesture-result');
    const effectBtn = document.getElementById('effect-btn');
    const faceBtn = document.getElementById('face-btn');
    
    // 获取统计按钮
    const refreshStatsBtn = document.getElementById('refresh-stats-btn');
    const resetStatsBtn = document.getElementById('reset-stats-btn');
    const saveStatsBtn = document.getElementById('save-stats-btn');
    
    // 获取统计显示元素
    const sessionDuration = document.getElementById('session-duration');
    const gestureStatsTable = document.getElementById('gesture-stats').querySelector('tbody');
    const expressionStatsTable = document.getElementById('expression-stats').querySelector('tbody');
    
    // 连接Socket.IO
    const socket = io({
        transports: ['websocket', 'polling'],  // 尝试WebSocket，如果失败则回退到polling
        reconnectionAttempts: 5,
        reconnectionDelay: 1000,
        timeout: 20000  // 增加超时时间
    });
    
    // 连接事件
    socket.on('connect', function() {
        console.log('已连接到服务器，ID:', socket.id);
        loadingIndicator.textContent = '已连接到服务器，点击"启动摄像头"按钮开始';
    });
    
    // 断开连接事件
    socket.on('disconnect', function() {
        console.log('与服务器断开连接');
        resetUI();
    });
    
    // 接收视频帧
    socket.on('frame', function(data) {
        // 显示视频帧
        videoFeed.src = data.image;
        videoFeed.style.display = 'block';
        loadingIndicator.style.display = 'none';
        
        // 更新手势识别结果
        let resultText = '';
        
        // 处理手势
        if (data.gestures && data.gestures.length > 0) {
            const gestureNames = data.gestures.map(gesture => getGestureName(gesture));
            resultText += '手势: ' + gestureNames.join(', ');
        } else {
            resultText += '手势: 未检测到';
        }
        
        // 处理面部表情
        if (data.expressions && data.expressions.length > 0) {
            const expressionNames = data.expressions.map(expression => getExpressionName(expression));
            resultText += '<br>表情: ' + expressionNames.join(', ');
        } else if (faceRecognitionEnabled) {
            resultText += '<br>表情: 未检测到';
        }
        
        gestureResult.innerHTML = resultText;
        gestureResult.style.color = resultText.includes('未检测到') ? '#f44336' : '#4caf50';
        
        // 更新统计数据
        if (data.stats) {
            updateStatsDisplay(data.stats);
        }
    });
    
    // 添加连接错误处理
    socket.on('connect_error', function(error) {
        console.error('连接错误:', error);
        alert('连接服务器失败，请刷新页面重试');
    });
    
    // 处理摄像头错误
    socket.on('camera_error', function(data) {
        console.error('摄像头错误:', data.message);
        alert('摄像头错误: ' + data.message);
        resetUI();
    });
    
    let effectEnabled = false;
    let faceRecognitionEnabled = false;
    
    // 特效按钮点击事件
    effectBtn.addEventListener('click', function() {
        socket.emit('toggle_effect', {}, function(response) {
            console.log('收到切换特效响应:', response);
            if (response && response.status === 'success') {
                effectEnabled = response.enabled;
                if (effectEnabled) {
                    effectBtn.textContent = '关闭黑客帝国特效';
                    effectBtn.classList.add('active');
                } else {
                    effectBtn.textContent = '开启黑客帝国特效';
                    effectBtn.classList.remove('active');
                }
            }
        });
    });
    
    // 面部识别按钮点击事件
    faceBtn.addEventListener('click', function() {
        socket.emit('toggle_face_recognition', {}, function(response) {
            console.log('收到切换面部识别响应:', response);
            if (response && response.status === 'success') {
                faceRecognitionEnabled = response.enabled;
                if (faceRecognitionEnabled) {
                    faceBtn.textContent = '关闭面部识别';
                    faceBtn.classList.add('active');
                } else {
                    faceBtn.textContent = '开启面部识别';
                    faceBtn.classList.remove('active');
                }
            }
        });
    });
    
    // 启动摄像头按钮点击事件
    startBtn.addEventListener('click', function() {
        console.log('点击启动摄像头按钮');
        loadingIndicator.style.display = 'block';
        loadingIndicator.textContent = '正在启动摄像头...';
        videoFeed.style.display = 'none';
        
        // 请求启动摄像头
        socket.emit('start_camera', {}, function(response) {
            console.log('收到启动摄像头响应:', response);
            if (response && response.status === 'success') {
                // 请求视频帧
                console.log('请求视频帧');
                socket.emit('request_frames');
                
                // 更新UI状态
                startBtn.disabled = true;
                stopBtn.disabled = false;
                effectBtn.disabled = false;  // 启用特效按钮
                faceBtn.disabled = false;    // 启用面部识别按钮
            } else {
                alert('启动摄像头失败: ' + (response?.message || '未知错误'));
                loadingIndicator.style.display = 'none';
            }
        });
    });
    
    // 停止摄像头按钮点击事件
    stopBtn.addEventListener('click', function() {
        // 请求停止摄像头
        socket.emit('stop_camera', {}, function(response) {
            resetUI();
        });
    });
    
    // 重置UI状态
    function resetUI() {
        videoFeed.style.display = 'none';
        loadingIndicator.style.display = 'block';
        loadingIndicator.textContent = '摄像头已停止';
        startBtn.disabled = false;
        stopBtn.disabled = true;
        effectBtn.disabled = true;  // 禁用特效按钮
        effectBtn.textContent = '开启黑客帝国特效';
        effectBtn.classList.remove('active');
        effectEnabled = false;
        faceBtn.disabled = true;    // 禁用面部识别按钮
        faceBtn.textContent = '开启面部识别';
        faceBtn.classList.remove('active');
        faceRecognitionEnabled = false;
        gestureResult.innerHTML = '等待识别...';
        gestureResult.style.color = '#333';
    }
    
    // 统计按钮点击事件
    refreshStatsBtn.addEventListener('click', function() {
        socket.emit('get_stats', {}, function(response) {
            if (response && response.status === 'success') {
                updateStatsDisplay(response.stats);
            }
        });
    });
    
    resetStatsBtn.addEventListener('click', function() {
        if (confirm('确定要重置所有统计数据吗？')) {
            socket.emit('reset_stats', {}, function(response) {
                if (response && response.status === 'success') {
                    alert('统计数据已重置');
                    // 清空统计表格
                    gestureStatsTable.innerHTML = '';
                    expressionStatsTable.innerHTML = '';
                    sessionDuration.textContent = '0分钟';
                }
            });
        }
    });
    
    saveStatsBtn.addEventListener('click', function() {
        socket.emit('save_stats', {}, function(response) {
            if (response && response.status === 'success') {
                alert('统计数据已保存');
            } else {
                alert('保存统计数据失败');
            }
        });
    });
    
    // 更新统计显示
    function updateStatsDisplay(stats) {
        if (!stats) return;
        
        // 更新会话时长
        sessionDuration.textContent = `${stats.session_duration.minutes}分钟 (${stats.session_duration.seconds}秒)`;
        
        // 更新手势统计
        gestureStatsTable.innerHTML = '';
        for (const gesture in stats.gestures.counts) {
            const count = stats.gestures.counts[gesture];
            const frequency = stats.gestures.frequencies[gesture] || 0;
            
            const row = document.createElement('tr');
            
            const gestureCell = document.createElement('td');
            gestureCell.textContent = getGestureName(gesture);
            
            const countCell = document.createElement('td');
            countCell.textContent = count;
            
            const frequencyCell = document.createElement('td');
            frequencyCell.textContent = frequency.toFixed(1);
            
            row.appendChild(gestureCell);
            row.appendChild(countCell);
            row.appendChild(frequencyCell);
            
            gestureStatsTable.appendChild(row);
        }
        
        // 更新表情统计
        expressionStatsTable.innerHTML = '';
        for (const expression in stats.expressions.counts) {
            const count = stats.expressions.counts[expression];
            const frequency = stats.expressions.frequencies[expression] || 0;
            
            const row = document.createElement('tr');
            
            const expressionCell = document.createElement('td');
            expressionCell.textContent = getExpressionName(expression);
            
            const countCell = document.createElement('td');
            countCell.textContent = count;
            
            const frequencyCell = document.createElement('td');
            frequencyCell.textContent = frequency.toFixed(1);
            
            row.appendChild(expressionCell);
            row.appendChild(countCell);
            row.appendChild(frequencyCell);
            
            expressionStatsTable.appendChild(row);
        }
    }
    
    // 获取手势中文名称
    function getGestureName(gesture) {
        switch(gesture) {
            case 'fist': return '握拳';
            case 'palm': return '手掌';
            case 'thumb_up': return '点赞';
            case 'peace': return '剪刀手';
            case 'pointing': return '指向';
            default: return gesture;
        }
    }
    
    // 获取表情中文名称
    function getExpressionName(expression) {
        switch(expression) {
            case 'smile': return '微笑';
            case 'blink': return '眨眼';
            default: return expression;
        }
    }
}); 