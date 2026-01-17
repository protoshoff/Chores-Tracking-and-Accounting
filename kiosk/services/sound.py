from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtCore import QUrl
import os

class SoundService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SoundService, cls).__new__(cls)
            cls._instance._init()
        return cls._instance
        
    def _init(self):
        self.effects = {}
        base_path = os.path.dirname(os.path.abspath(__file__))
        self.assets_path = os.path.join(base_path, "../assets/sounds")
        
        # Preload common sounds
        self._load("click", "click.wav")
        self._load("success", "success.wav")
        self._load("error", "error.wav")
        
    def _load(self, name, filename):
        path = os.path.join(self.assets_path, filename)
        if os.path.exists(path):
            effect = QSoundEffect()
            effect.setSource(QUrl.fromLocalFile(path))
            effect.setVolume(0.5) 
            self.effects[name] = effect
        else:
            print(f"Warning: Sound file not found: {path}")

    def play(self, name):
        if name in self.effects:
            self.effects[name].play()
            
    @staticmethod
    def play_click():
        SoundService().play("click")

    @staticmethod
    def play_success():
        SoundService().play("success")
        
    @staticmethod
    def play_error():
        SoundService().play("error")
