from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, filters
from bot.config import config
import os

def setup_handlers(application, bot):
    """Настройка всех обработчиков"""
    
    # Команды
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("upload_base", upload_base_command))
    application.add_handler(CommandHandler("reset", reset_command))
    application.add_handler(CommandHandler("status", status_command))
    
    # Обработка документов (загрузка базы знаний)
    application.add_handler(MessageHandler(
        filters.Document.ALL, 
        handle_document
    ))
    
    # Обработка текстовых сообщений
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message
    ))
    
    # Обработка callback кнопок
    application.add_handler(CallbackQueryHandler(button_handler))

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    keyboard = get_main_keyboard()
    
    welcome_text = """
🤖 Добро пожаловать в AI-ассистент Мосэнергосбыт!

Я помогу вам найти ответы на вопросы, используя базу знаний компании.

Доступные команды:
/help - показать справку
/upload_base - загрузить базу знаний (только для админов)
/status - статус системы

Используйте кнопки ниже для быстрого доступа к функциям.
    """
    
    await update.message.reply_text(welcome_text, reply_markup=keyboard)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
📖 Справка по использованию бота:

Основные команды:
/start - начать работу
/help - показать эту справку
/upload_base - загрузить базу знаний
/reset - сбросить базу знаний
/status - статус системы

Как использовать:
1. Администратор загружает базу знаний через кнопку "📂 Загрузить базу знаний"
2. Задавайте вопросы в свободной форме на русском языке
3. Бот найдет наиболее релевантные ответы в базе знаний

Поддерживаемые форматы файлов: .txt, .csv, .json
    """
    
    await update.message.reply_text(help_text, reply_markup=get_main_keyboard())

async def upload_base_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды загрузки базы знаний"""
    user_id = update.effective_user.id
    
    if user_id not in config.ADMINS:
        await update.message.reply_text("❌ У вас нет прав для загрузки базы знаний.")
        return
        
    await update.message.reply_text(
        "📂 Пожалуйста, загрузите файл с базой знаний (формат: .txt, .csv, .json)",
        reply_markup=get_upload_keyboard()
    )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка загруженных документов"""
    user_id = update.effective_user.id
    
    if user_id not in config.ADMINS:
        await update.message.reply_text("❌ У вас нет прав для загрузки файлов.")
        return
        
    document = update.message.document
    file_extension = document.file_name.split('.')[-1].lower()
    
    if file_extension not in ['txt', 'csv', 'json']:
        await update.message.reply_text("❌ Неподдерживаемый формат файла. Используйте .txt, .csv или .json")
        return
        
    # Скачивание файла
    file = await document.get_file()
    file_path = os.path.join(config.KNOWLEDGE_BASE_DIR, document.file_name)
    await file.download_to_drive(file_path)
    
    # Обработка файла
    await process_knowledge_base(file_path, update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""
    user_message = update.message.text
    
    try:
        # Поиск релевантной информации
        results = await context.bot_data['semantic_search'].search(user_message)
        
        if results:
            # Генерация ответа с использованием DeepPavlov
            answer = await context.bot_data['dp_model'].generate_answer(
                user_message, 
                results
            )
            await update.message.reply_text(answer)
        else:
            await update.message.reply_text(
                "🤔 Извините, я не нашел подходящей информации в базе знаний. "
                "Попробуйте переформулировать вопрос или загрузите базу знаний."
            )
            
    except Exception as e:
        logging.error(f"Ошибка обработки сообщения: {e}")
        await update.message.reply_text(
            "⚠️ Произошла ошибка при обработке запроса. Попробуйте позже."
        )

def get_main_keyboard():
    """Клавиатура основного меню"""
    keyboard = [
        [
            InlineKeyboardButton("📂 Загрузить базу знаний", callback_data='upload_base'),
            InlineKeyboardButton("🔍 Найти ответ", callback_data='search')
        ],
        [InlineKeyboardButton("♻️ Перезапустить", callback_data='reset')],
        [InlineKeyboardButton("📊 Статус", callback_data='status')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_upload_keyboard():
    """Клавиатура для загрузки"""
    keyboard = [
        [InlineKeyboardButton("❌ Отмена", callback_data='cancel_upload')]
    ]
    return InlineKeyboardMarkup(keyboard)
