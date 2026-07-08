import pygame

def init_audio():
    try:
        pygame.mixer.init()
        print("✅ Audio: OK")
    except Exception as e:
        print(f"❌ Audio lỗi: {e}")