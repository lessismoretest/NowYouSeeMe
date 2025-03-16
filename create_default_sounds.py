import os
import pygame
import pygame.sndarray
import numpy as np

# 初始化pygame
pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)

# 创建音效目录
if not os.path.exists('static/sounds'):
    os.makedirs('static/sounds')

# 创建默认音效
def create_sound(name, freq=440, duration=0.5):
    """创建一个简单的音效"""
    sample_rate = 44100
    sound_array = np.zeros((int(sample_rate * duration),), dtype=np.int16)
    
    # 根据不同的音效类型生成不同的声音
    if name == 'start':
        # 上升音调
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        freq_array = np.linspace(220, 880, int(sample_rate * duration))
        sound_array = (32767 * 0.5 * np.sin(2 * np.pi * freq_array * t / sample_rate)).astype(np.int16)
    elif name == 'eat':
        # 短促高音
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        sound_array = (32767 * 0.5 * np.sin(2 * np.pi * 880 * t) * np.exp(-5 * t)).astype(np.int16)
    elif name == 'direction':
        # 短促咔嗒声
        sound_array[:int(sample_rate * 0.1)] = (32767 * 0.3 * np.random.uniform(-1, 1, size=int(sample_rate * 0.1))).astype(np.int16)
    elif name == 'game_over':
        # 下降音调
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        freq_array = np.linspace(880, 220, int(sample_rate * duration))
        sound_array = (32767 * 0.5 * np.sin(2 * np.pi * freq_array * t / sample_rate)).astype(np.int16)
    elif name == 'pause':
        # 两个短音
        t1 = np.linspace(0, duration/4, int(sample_rate * duration/4), False)
        t2 = np.linspace(0, duration/4, int(sample_rate * duration/4), False)
        sound1 = (32767 * 0.5 * np.sin(2 * np.pi * 660 * t1)).astype(np.int16)
        sound2 = (32767 * 0.5 * np.sin(2 * np.pi * 440 * t2)).astype(np.int16)
        sound_array[:len(sound1)] = sound1
        sound_array[len(sound1):len(sound1)+len(sound2)] = sound2
    elif name == 'resume':
        # 两个短音（反向）
        t1 = np.linspace(0, duration/4, int(sample_rate * duration/4), False)
        t2 = np.linspace(0, duration/4, int(sample_rate * duration/4), False)
        sound1 = (32767 * 0.5 * np.sin(2 * np.pi * 440 * t1)).astype(np.int16)
        sound2 = (32767 * 0.5 * np.sin(2 * np.pi * 660 * t2)).astype(np.int16)
        sound_array[:len(sound1)] = sound1
        sound_array[len(sound1):len(sound1)+len(sound2)] = sound2
    else:
        # 默认音效
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        sound_array = (32767 * 0.5 * np.sin(2 * np.pi * freq * t)).astype(np.int16)
    
    # 创建pygame声音对象
    sound = pygame.sndarray.make_sound(sound_array)
    
    # 保存为WAV文件
    path = f'static/sounds/{name}.wav'
    pygame.mixer.Sound.save(sound, path)
    print(f"已创建音效: {path}")

# 创建所有默认音效
sounds = ['start', 'eat', 'direction', 'game_over', 'pause', 'resume']
for sound_name in sounds:
    create_sound(sound_name)

print("所有默认音效已创建完成") 