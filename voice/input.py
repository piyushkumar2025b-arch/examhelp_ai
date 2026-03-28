from utils.app_controller import AppController

class VoiceInput:
    @staticmethod
    def listen():
        r = AppController.voice_input()
        return r
