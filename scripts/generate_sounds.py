import wave
import math
import struct
import os

def generate_tone(filename, frequency=440, duration=0.1, volume=0.5, sample_rate=44100, wave_type='sine'):
    n_samples = int(sample_rate * duration)
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1) # Mono
        wav_file.setsampwidth(2) # 2 bytes (16-bit)
        wav_file.setframerate(sample_rate)
        
        for i in range(n_samples):
            t = float(i) / sample_rate
            
            # Envelope (Attack/Decay)
            if i < 500: # Attack
                env = i / 500.0
            elif i > n_samples - 500: # Decay
                env = (n_samples - i) / 500.0
            else:
                env = 1.0
                
            if wave_type == 'sine':
                value = math.sin(2.0 * math.pi * frequency * t)
            elif wave_type == 'square':
                value = 1.0 if math.sin(2.0 * math.pi * frequency * t) > 0 else -1.0
            elif wave_type == 'saw':
                 period = 1.0 / frequency
                 value = 2.0 * (t / period - math.floor(t / period + 0.5))
            
            # Apply volume and envelope
            sample = int(value * 32767.0 * volume * env)
            wav_file.writeframes(struct.pack('<h', sample))

def generate_click(filename):
    # Short high pitch blip
    generate_tone(filename, frequency=1200, duration=0.05, volume=0.3, wave_type='sine')

def generate_success(filename):
    # Rising Arpeggio (Major Triad)
    sample_rate = 44100
    duration = 0.1
    c5 = 523.25
    e5 = 659.25
    g5 = 783.99
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        
        for freq in [c5, e5, g5]:
            n_samples = int(sample_rate * duration)
            for i in range(n_samples):
                t = float(i) / sample_rate
                # Quick decay
                env = 1.0 - (i / n_samples)
                value = math.sin(2.0 * math.pi * freq * t)
                sample = int(value * 32767.0 * 0.4 * env)
                wav_file.writeframes(struct.pack('<h', sample))

def generate_error(filename):
    # Low buzz/saw
    generate_tone(filename, frequency=150, duration=0.3, volume=0.4, wave_type='saw')

if __name__ == "__main__":
    base_dir = "kiosk/assets/sounds"
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
        
    print("Generating sounds...")
    generate_click(f"{base_dir}/click.wav")
    generate_success(f"{base_dir}/success.wav")
    generate_error(f"{base_dir}/error.wav")
    print("Done.")
