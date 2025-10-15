
import os
from typing import List

class Config:
    # Telegram Bot Configuration
    BOT_TOKEN = "8220943151:AAEn4NUhoRU4GiTduA13DZffhlet0OjW8JE"
    ADMIN_IDS = [1206716741, 7807660296, 6910167987, 495779404]
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    KNOWLEDGE_BASE_DIR = os.path.join(DATA_DIR, "knowledge_base")
    EMBEDDINGS_DB = os.path.join(DATA_DIR, "embeddings.db")
    
    # DeepPavlov Configuration
    DEEPPAVLOV_MODEL = "ru_bert"
    MAX_SEQUENCE_LENGTH = 512
    
    # GoMLX Configuration
    GOMLX_HOST = "localhost"
    GOMLX_PORT = 8080
    
    # File Upload Settings
    MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB
    ALLOWED_EXTENSIONS = {'.txt', '.csv', '.json'}
    
    # Semantic Search
    TOP_K_RESULTS = 3
    SIMILARITY_THRESHOLD = 0.7

config = Config()
