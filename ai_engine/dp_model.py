import logging
from deeppavlov import build_model, configs
from deeppavlov.core.common.file import read_json
import asyncio
import os
from bot.config import config

logger = logging.getLogger(__name__)

class DeepPavlovModel:
    def __init__(self):
        self.model = None
        self.embedder = None
        
    async def load_model(self):
        """Загрузка модели DeepPavlov для русского языка"""
        try:
            # Используем предобученную модель для русского языка
            model_config = read_json(configs.embedder.bert_embedder)
            model_config['metadata']['variables']['BERT_MODEL_PATH'] = config.MODELS_DIR
            
            self.model = build_model(model_config, download=True)
            logger.info("DeepPavlov модель успешно загружена")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки модели DeepPavlov: {e}")
            raise
            
    async def generate_answer(self, question: str, context_results: list) -> str:
        """Генерация ответа на основе контекста"""
        try:
            # Объединяем контекстные результаты
            context = "\n".join([result['text'] for result in context_results])
            
            # Формируем промпт для модели
            prompt = f"""
            Контекст: {context}
            
            Вопрос: {question}
            
            Ответь на русском языке на основе предоставленного контекста. 
            Будь точным и информативным. Если в контексте нет точного ответа, 
            скажи об этом честно.
            """
            
            # Генерация ответа (упрощенная версия)
            # В реальной реализации здесь будет вызов модели
            answer = self._simplified_answer(question, context)
            
            return answer
            
        except Exception as e:
            logger.error(f"Ошибка генерации ответа: {e}")
            return "Извините, произошла ошибка при генерации ответа."
            
    def _simplified_answer(self, question: str, context: str) -> str:
        """Упрощенная версия генерации ответа (заглушка)"""
        # В реальной реализации здесь будет полноценная генерация
        # через DeepPavlov модель
        
        # Поиск наиболее релевантного фрагмента
        lines = context.split('\n')
        relevant_lines = []
        
        question_words = set(question.lower().split())
        
        for line in lines:
            line_words = set(line.lower().split())
            if len(question_words.intersection(line_words)) > 0:
                relevant_lines.append(line)
                
        if relevant_lines:
            return "\n".join(relevant_lines[:3])  # Возвращаем первые 3 релевантные строки
        else:
            return "К сожалению, в базе знаний нет точного ответа на ваш вопрос."
