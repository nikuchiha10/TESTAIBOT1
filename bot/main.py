import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ContextTypes, filters
)
from bot.config import config
from bot.handlers import setup_handlers
from ai_engine.dp_model import DeepPavlovModel
from ai_engine.semantic_search import SemanticSearch

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class RussianAIBot:
    def __init__(self):
        self.dp_model = None
        self.semantic_search = None
        self.app = None
        
    async def initialize_ai(self):
        """Инициализация AI моделей"""
        try:
            self.dp_model = DeepPavlovModel()
            await self.dp_model.load_model()
            
            self.semantic_search = SemanticSearch()
            await self.semantic_search.initialize()
            
            logger.info("AI модели успешно инициализированы")
            return True
        except Exception as e:
            logger.error(f"Ошибка инициализации AI: {e}")
            return False
            
    async def start_bot(self):
        """Запуск бота"""
        self.app = Application.builder().token(config.TOKEN).build()
        
        # Инициализация AI
        if not await self.initialize_ai():
            logger.error("Не удалось инициализировать AI модели")
            return
            
        # Настройка обработчиков
        setup_handlers(self.app, self)
        
        # Запуск бота
        await self.app.run_polling()

def main():
    bot = RussianAIBot()
    asyncio.run(bot.start_bot())

if __name__ == "__main__":
    main()
