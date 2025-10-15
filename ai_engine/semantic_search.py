import logging
import sqlite3
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import json
from typing import List, Dict
from bot.config import config

logger = logging.getLogger(__name__)

class SemanticSearch:
    def __init__(self):
        self.embedder = None
        self.index = None
        self.documents = []
        self.db_conn = None
        
    async def initialize(self):
        """Инициализация семантического поиска"""
        try:
            # Загрузка модели для эмбеддингов
            self.embedder = SentenceTransformer(config.EMBEDDING_MODEL)
            
            # Инициализация FAISS индекса
            self.index = faiss.IndexFlatL2(384)  # Размерность для multilingual-MiniLM
            
            # Подключение к базе данных
            self.db_conn = sqlite3.connect(config.EMBEDDINGS_DB)
            self._create_tables()
            
            # Загрузка существующих эмбеддингов
            await self._load_existing_embeddings()
            
            logger.info("Семантический поиск инициализирован")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации семантического поиска: {e}")
            raise
            
    async def add_documents(self, documents: List[Dict]):
        """Добавление документов в поисковый индекс"""
        try:
            texts = [doc['text'] for doc in documents]
            
            # Создание эмбеддингов
            embeddings = self.embedder.encode(texts)
            
            # Добавление в FAISS индекс
            self.index.add(embeddings.astype('float32'))
            self.documents.extend(documents)
            
            # Сохранение в базу данных
            await self._save_to_database(documents, embeddings)
            
            logger.info(f"Добавлено {len(documents)} документов в индекс")
            
        except Exception as e:
            logger.error(f"Ошибка добавления документов: {e}")
            raise
            
    async def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Поиск релевантных документов"""
        try:
            # Создание эмбеддинга для запроса
            query_embedding = self.embedder.encode([query])
            
            # Поиск в индексе
            distances, indices = self.index.search(
                query_embedding.astype('float32'), 
                min(top_k, len(self.documents))
            )
            
            # Формирование результатов
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.documents):
                    results.append({
                        'text': self.documents[idx]['text'],
                        'score': float(1 - distances[0][i]),  # Конвертация расстояния в схожесть
                        'source': self.documents[idx].get('source', 'unknown')
                    })
                    
            # Фильтрация по порогу схожести
            filtered_results = [
                r for r in results 
                if r['score'] >= config.SIMILARITY_THRESHOLD
            ]
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")
            return []
            
    def _create_tables(self):
        """Создание таблиц в базе данных"""
        cursor = self.db_conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                source TEXT,
                embedding BLOB
            )
        ''')
        
        self.db_conn.commit()
        
    async def _save_to_database(self, documents: List[Dict], embeddings: np.ndarray):
        """Сохранение документов и эмбеддингов в базу данных"""
        cursor = self.db_conn.cursor()
        
        for i, doc in enumerate(documents):
            # Сериализация эмбеддинга
            embedding_blob = embeddings[i].astype('float32').tobytes()
            
            cursor.execute('''
                INSERT INTO documents (text, source, embedding)
                VALUES (?, ?, ?)
            ''', (doc['text'], doc.get('source', 'unknown'), embedding_blob))
            
        self.db_conn.commit()
        
    async def _load_existing_embeddings(self):
        """Загрузка существующих эмбеддингов из базы данных"""
        cursor = self.db_conn.cursor()
        
        cursor.execute('SELECT text, source, embedding FROM documents')
        rows = cursor.fetchall()
        
        embeddings_list = []
        documents_list = []
        
        for row in rows:
            text, source, embedding_blob = row
            
            # Десериализация эмбеддинга
            embedding = np.frombuffer(embedding_blob, dtype='float32')
            embeddings_list.append(embedding)
            
            documents_list.append({
                'text': text,
                'source': source
            })
            
        if embeddings_list:
            embeddings_array = np.array(embeddings_list)
            self.index.add(embeddings_array)
            self.documents = documents_list
            
        logger.info(f"Загружено {len(documents_list)} документов из базы данных")
