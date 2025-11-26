import os

class Settings:
    """Настройки приложения"""
    def __init__(self):
        self.GIGACHAT_CREDENTIALS = os.getenv("GIGACHAT_CREDENTIALS", "")
        self.GIGACHAT_SCOPE = os.getenv("GIGACHAT_SCOPE", "")
        self.GIGACHAT_MODEL = os.getenv("GIGACHAT_MODEL", "")
        self.CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

settings = Settings()