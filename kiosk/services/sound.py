"""Sound effects service for kiosk UI."""
import os
import struct
import math
import wave

# Sound assets directory
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "sounds")


def _generate_tone(filename, freq=440, duration_ms=200, volume=0.5, fade_ms=20, waveform="sine"):
    """Generate a simple WAV tone file if it doesn't exist."""
    if os.path.exists(filename):
        return
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    sample_rate = 22050
    n_samples = int(sample_rate * duration_ms / 1000)
    fade_samples = int(sample_rate * fade_ms / 1000)
    
    samples = []
    for i in range(n_samples):
        t = i / sample_rate
        if waveform == "sine":
            val = math.sin(2 * math.pi * freq * t)
        elif waveform == "square":
            val = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
        else:
            val = math.sin(2 * math.pi * freq * t)
        
        # Apply fade in/out
        if i < fade_samples:
            val *= i / fade_samples
        elif i > n_samples - fade_samples:
            val *= (n_samples - i) / fade_samples
        
        val = int(val * volume * 32767)
        samples.append(struct.pack('<h', max(-32768, min(32767, val))))
    
    with wave.open(filename, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b''.join(samples))


def _generate_multi_tone(filename, tones, volume=0.4):
    """Generate a WAV with multiple sequential tones. tones = [(freq, duration_ms), ...]"""
    if os.path.exists(filename):
        return
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    sample_rate = 22050
    all_samples = []
    
    for freq, duration_ms in tones:
        n_samples = int(sample_rate * duration_ms / 1000)
        fade = int(sample_rate * 10 / 1000)
        for i in range(n_samples):
            t = i / sample_rate
            val = math.sin(2 * math.pi * freq * t)
            if i < fade:
                val *= i / fade
            elif i > n_samples - fade:
                val *= (n_samples - i) / fade
            val = int(val * volume * 32767)
            all_samples.append(struct.pack('<h', max(-32768, min(32767, val))))
    
    with wave.open(filename, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b''.join(all_samples))


def _ensure_sounds():
    """Generate all sound effects if they don't exist."""
    # Click — short high blip
    _generate_tone(os.path.join(ASSETS_DIR, "click.wav"), freq=800, duration_ms=50, volume=0.3)
    
    # Success — ascending two-tone
    _generate_multi_tone(os.path.join(ASSETS_DIR, "success.wav"), [(523, 120), (659, 120), (784, 200)])
    
    # Error — low buzz
    _generate_tone(os.path.join(ASSETS_DIR, "error.wav"), freq=200, duration_ms=300, volume=0.4, waveform="square")
    
    # Chore complete — cheerful ding
    _generate_multi_tone(os.path.join(ASSETS_DIR, "chore_complete.wav"), [(660, 100), (880, 200)])
    
    # Approval — bright ascending
    _generate_multi_tone(os.path.join(ASSETS_DIR, "approval.wav"), [(523, 80), (659, 80), (784, 80), (1047, 250)])
    
    # Payout — cash register feel
    _generate_multi_tone(os.path.join(ASSETS_DIR, "payout.wav"), [(1047, 60), (1319, 60), (1568, 60), (2093, 300)])
    
    # Navigation — soft click
    _generate_tone(os.path.join(ASSETS_DIR, "nav.wav"), freq=600, duration_ms=40, volume=0.2)


class SoundService:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(self):
        """Call once after QApplication is created."""
        if self._initialized:
            return
        self._initialized = True
        
        _ensure_sounds()
        
        self.effects = {}
        try:
            from PySide6.QtMultimedia import QSoundEffect
            from PySide6.QtCore import QUrl
            
            for name in ["click", "success", "error", "chore_complete", "approval", "payout", "nav"]:
                path = os.path.join(ASSETS_DIR, f"{name}.wav")
                if os.path.exists(path):
                    effect = QSoundEffect()
                    effect.setSource(QUrl.fromLocalFile(os.path.abspath(path)))
                    effect.setVolume(0.5)
                    self.effects[name] = effect
        except ImportError:
            print("Warning: QSoundEffect not available — sounds disabled")
            self.effects = {}

    def play(self, name):
        if not self._initialized:
            self.initialize()
        effect = self.effects.get(name)
        if effect:
            effect.play()

    @staticmethod
    def play_click():
        SoundService().play("click")

    @staticmethod
    def play_success():
        SoundService().play("success")

    @staticmethod
    def play_error():
        SoundService().play("error")

    @staticmethod
    def play_chore_complete():
        SoundService().play("chore_complete")

    @staticmethod
    def play_approval():
        SoundService().play("approval")

    @staticmethod
    def play_payout():
        SoundService().play("payout")

    @staticmethod
    def play_nav():
        SoundService().play("nav")
