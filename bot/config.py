import os
from typing import List

class BotConfig:
    TOKEN = "8220943151:AAEn4NUhoRU4GiTduA13DZffhlet0OjW8JE"
    ADMINS = [1206716741, 7807660296, 6910167987, 495779404]
    LANGUAGE = "ru"
    
    # Пути к данным
    DATA_DIR = "data"
    KNOWLEDGE_BASE_DIR = os.path.join(DATA_DIR, "knowledge_base")
    MODELS_DIR = os.path.join(DATA_DIR, "models")
    EMBEDDINGS_DB = os.path.join(DATA_DIR, "embeddings.db")
    
    # Настройки DeepPavlov
    DP_MODEL_NAME = "ru_bert"
    EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    
    # Настройки поиска
    SIMILARITY_THRESHOLD = 0.7
    MAX_RESULTS = 5

config = BotConfig()
