import wave
import math
import struct
import random
import os

# 설정
SAMPLE_RATE = 44100
AMPLITUDE = 16000 # 16-bit audio (max 32767)

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def save_wav(filename, data):
    with wave.open(filename, 'w') as f:
        f.setnchannels(1) # Mono
        f.setsampwidth(2) # 2 bytes (16-bit)
        f.setframerate(SAMPLE_RATE)
        f.writeframes(data)
    print(f"Generated: {filename}")

# --- 파형 생성 함수들 ---

def generate_sine_wave(freq, duration, vol=1.0):
    n_frames = int(SAMPLE_RATE * duration)
    data = bytearray()
    for i in range(n_frames):
        t = i / SAMPLE_RATE
        value = int(AMPLITUDE * vol * math.sin(2 * math.pi * freq * t))
        data += struct.pack('<h', max(-32767, min(32767, value)))
    return data

def generate_square_wave(freq, duration, vol=1.0):
    n_frames = int(SAMPLE_RATE * duration)
    data = bytearray()
    period = int(SAMPLE_RATE / freq)
    for i in range(n_frames):
        value = int(AMPLITUDE * vol * (1 if (i // (period // 2)) % 2 else -1))
        data += struct.pack('<h', value)
    return data

def generate_noise(duration, vol=1.0, decay=False):
    n_frames = int(SAMPLE_RATE * duration)
    data = bytearray()
    for i in range(n_frames):
        env = 1.0
        if decay: env = 1.0 - (i / n_frames)
        value = int(AMPLITUDE * vol * env * random.uniform(-1, 1))
        data += struct.pack('<h', value)
    return data

def generate_sawtooth(freq, duration, vol=1.0):
    n_frames = int(SAMPLE_RATE * duration)
    data = bytearray()
    period = SAMPLE_RATE / freq
    for i in range(n_frames):
        value = int(AMPLITUDE * vol * (2 * ((i % period) / period) - 1))
        data += struct.pack('<h', value)
    return data

# --- 복합 사운드 생성 ---

def sfx_jump(duration=0.3):
    # 주파수가 올라가는 Sine 파형
    n_frames = int(SAMPLE_RATE * duration)
    data = bytearray()
    for i in range(n_frames):
        t = i / SAMPLE_RATE
        freq = 200 + (400 * (t / duration))
        value = int(AMPLITUDE * 0.5 * math.sin(2 * math.pi * freq * t))
        data += struct.pack('<h', value)
    return data

def sfx_coin():
    # 띠-링 (두 개의 높은음)
    part1 = generate_sine_wave(1200, 0.1, 0.5)
    part2 = generate_sine_wave(1800, 0.2, 0.5)
    return part1 + part2

def sfx_shoot():
    # 노이즈 + 급격한 감소
    return generate_noise(0.2, vol=0.8, decay=True)

def sfx_explosion():
    # 낮은 주파수 노이즈 (다운샘플링 느낌) + 긴 감소
    n_frames = int(SAMPLE_RATE * 1.0)
    data = bytearray()
    last_val = 0
    for i in range(n_frames):
        if i % 4 == 0: # 4배 느리게 갱신 -> 저음 효과
            last_val = random.uniform(-1, 1)
        env = 1.0 - (i / n_frames)**2
        value = int(AMPLITUDE * 0.8 * env * last_val)
        data += struct.pack('<h', value)
    return data

def sfx_siren():
    # 주파수 변조 (LFO)
    duration = 2.0
    n_frames = int(SAMPLE_RATE * duration)
    data = bytearray()
    for i in range(n_frames):
        t = i / SAMPLE_RATE
        # 1초에 2번 울리는 사이렌
        freq = 600 + 300 * math.sin(2 * math.pi * 2 * t)
        value = int(AMPLITUDE * 0.5 * ((i % int(SAMPLE_RATE/freq))/(SAMPLE_RATE/freq) * 2 - 1)) # Sawtooth
        data += struct.pack('<h', value)
    return data

def sfx_footstep():
    # 아주 짧은 저음 노이즈
    n_frames = int(SAMPLE_RATE * 0.05)
    data = bytearray()
    for i in range(n_frames):
        val = random.uniform(-1, 1)
        if i % 2 == 0: val *= -1 # High pass filter effect? No, just noise
        value = int(AMPLITUDE * 0.3 * (1 - i/n_frames) * val)
        data += struct.pack('<h', value)
    return data

def bgm_title():
    # 몽환적인 아르페지오 (C Major7) - 8초 루프
    # C4, E4, G4, B4
    notes = [261.63, 329.63, 392.00, 493.88]
    data = bytearray()
    # 4번 반복
    for _ in range(4):
        for note in notes:
            # 약간의 에코 효과를 위해 decay가 있는 sine wave
            chunk = generate_sine_wave(note, 0.2, 0.3)
            data += chunk
    return data

def bgm_game():
    # 긴장감 있는 베이스 라인 (A Minor) - 8초 루프
    # A2, A2, C3, A2 ...
    notes = [110.00, 110.00, 130.81, 110.00, 146.83, 110.00, 130.81, 123.47]
    data = bytearray()
    for _ in range(4): # 반복
        for note in notes:
            # Square wave for retro bass
            chunk = generate_square_wave(note, 0.2, 0.2)
            data += chunk
    return data

def main():
    base_dir = "assets/sounds"
    sfx_dir = os.path.join(base_dir, "sfx")
    bgm_dir = os.path.join(base_dir, "bgm")
    
    ensure_dir(sfx_dir)
    ensure_dir(bgm_dir)

    # --- SFX 생성 ---
    save_wav(os.path.join(sfx_dir, "FOOTSTEP.wav"), sfx_footstep())
    save_wav(os.path.join(sfx_dir, "RUN.wav"), generate_noise(0.15, 0.4, True))
    save_wav(os.path.join(sfx_dir, "RUSTLE.wav"), generate_noise(0.3, 0.2, True))
    
    save_wav(os.path.join(sfx_dir, "DOOR_OPEN.wav"), generate_sawtooth(100, 0.3, 0.4)) # 끼익? (낮은 톱니파)
    save_wav(os.path.join(sfx_dir, "DOOR_CLOSE.wav"), generate_noise(0.2, 0.6, True)) # 쿵
    save_wav(os.path.join(sfx_dir, "DOOR_LOCK.wav"), generate_square_wave(800, 0.1, 0.4) + generate_square_wave(600, 0.1, 0.4)) # 철컥

    save_wav(os.path.join(sfx_dir, "GUNSHOT.wav"), sfx_shoot())
    save_wav(os.path.join(sfx_dir, "RELOAD.wav"), generate_noise(0.1, 0.3) + generate_noise(0.1, 0.3))
    save_wav(os.path.join(sfx_dir, "SLASH.wav"), generate_noise(0.2, 0.3, True)) # 쉭 (White noise decay)
    save_wav(os.path.join(sfx_dir, "HIT.wav"), generate_square_wave(100, 0.1, 0.6)) # 퍽
    save_wav(os.path.join(sfx_dir, "DEATH.wav"), generate_sawtooth(200, 0.5, 0.5) + generate_sawtooth(100, 0.5, 0.3)) # 으악 (Tone drop)
    save_wav(os.path.join(sfx_dir, "SIREN.wav"), sfx_siren())
    save_wav(os.path.join(sfx_dir, "EXPLOSION.wav"), sfx_explosion())

    save_wav(os.path.join(sfx_dir, "EAT.wav"), generate_noise(0.1, 0.3) + generate_noise(0.1, 0.3))
    save_wav(os.path.join(sfx_dir, "DRINK.wav"), generate_sine_wave(300, 0.1) + generate_sine_wave(400, 0.1))
    save_wav(os.path.join(sfx_dir, "HEAL.wav"), generate_sine_wave(400, 0.5, 0.4)) # 치이익? (Sine up?)
    save_wav(os.path.join(sfx_dir, "ITEM_GET.wav"), sfx_coin()) # 띠링
    save_wav(os.path.join(sfx_dir, "COIN_GET.wav"), sfx_coin())
    save_wav(os.path.join(sfx_dir, "WORK.wav"), generate_square_wave(150, 0.1, 0.4)) # 뚝
    save_wav(os.path.join(sfx_dir, "ERROR.wav"), generate_square_wave(100, 0.3, 0.5)) # 삐빅

    save_wav(os.path.join(sfx_dir, "CLICK.wav"), generate_sine_wave(800, 0.05, 0.2))
    save_wav(os.path.join(sfx_dir, "HOVER.wav"), generate_sine_wave(600, 0.02, 0.1))
    save_wav(os.path.join(sfx_dir, "ALERT.wav"), generate_square_wave(1200, 0.1, 0.4) + generate_square_wave(1000, 0.2, 0.4))
    save_wav(os.path.join(sfx_dir, "VOTE.wav"), generate_sine_wave(1000, 0.3, 0.4))
    save_wav(os.path.join(sfx_dir, "PHASE_CHANGE.wav"), generate_sine_wave(440, 1.0, 0.3)) # 긴 톤

    # --- BGM 생성 ---
    save_wav(os.path.join(bgm_dir, "TITLE_THEME.wav"), bgm_title())
    save_wav(os.path.join(bgm_dir, "GAME_THEME.wav"), bgm_game())

if __name__ == "__main__":
    main()
