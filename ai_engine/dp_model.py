import torch
from deeppavlov import build_model, configs
from loguru import logger
from typing import List, Dict
from config import config

class DeepPavlovEngine:
    def __init__(self):
        self.qa_model = None
        self.embedding_model = None
        self.load_models()
    
    def load_models(self):
        """Load DeepPavlov models"""
        try:
            logger.info("Loading DeepPavlov models...")
            
            # Load QA model for Russian
            self.qa_model = build_model(configs.squad.squad_ru_bert, download=True)
            
            logger.info("DeepPavlov models loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading DeepPavlov models: {e}")
            raise
    
    def process_query(self, query: str, context: str = None) -> str:
        """Process user query and generate response"""
        try:
            # If no context provided, use default response
            if not context:
                return self._generate_fallback_response(query)
            
            # Use QA model with context
            result = self.qa_model([context], [query])
            answer = result[0][0] if result[0] else "Извините, я не нашел точного ответа на ваш вопрос в предоставленной информации."
            
            return self._format_response(answer, query)
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return "Извините, произошла ошибка при обработке вашего запроса."
    
    def _generate_fallback_response(self, query: str) -> str:
        """Generate fallback response when no context is available"""
        fallback_responses = [
            "На основе доступной информации я не могу дать точный ответ на ваш вопрос. "
            "Пожалуйста, убедитесь, что база знаний загружена и содержит релевантную информацию.",
            
            "Для ответа на этот вопрос мне нужна дополнительная информация из базы знаний. "
            "Пожалуйста, обратитесь к администратору для загрузки соответствующих данных.",
            
            "В настоящее время у меня недостаточно информации для ответа на этот вопрос. "
            "Загрузите базу знаний с соответствующей информацией для получения точных ответов."
        ]
        
        return fallback_responses[hash(query) % len(fallback_responses)]
    
    def _format_response(self, answer: str, original_query: str) -> str:
        """Format the final response"""
        response = f"🔍 **Ответ на ваш вопрос:**\n\n{answer}\n\n"
        
        # Add suggestions for follow-up
        response += "💡 *Если ответ неполный, попробуйте переформулировать вопрос или уточнить детали.*"
        
        return response

class RussianTextProcessor:
    """Utility class for Russian text processing"""
    
    @staticmethod
    def preprocess_text(text: str) -> str:
        """Preprocess Russian text"""
        # Basic preprocessing
        text = text.strip()
        text = ' '.join(text.split())  # Normalize whitespace
        return text
    
    @staticmethod
    def is_russian(text: str, threshold: float = 0.6) -> bool:
        """Check if text is primarily Russian"""
        russian_chars = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюя')
        text_chars = set(text.lower())
        
        russian_count = sum(1 for char in text_chars if char in russian_chars)
        total_count = len(text_chars)
        
        if total_count == 0:
            return False
            
        return (russian_count / total_count) >= threshold
