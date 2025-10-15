from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from config import config
from loguru import logger
import psutil
import os
from datetime import datetime

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in config.ADMIN_IDS

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user_id = update.effective_user.id
    username = update.effective_user.first_name
    
    welcome_text = (
        f"Привет, {username}! 👋\n\n"
        "Я - автономный AI-ассистент с поддержкой русского языка.\n"
        "Я могу отвечать на вопросы на основе загруженной базы знаний.\n\n"
        "Доступные команды:\n"
        "/start - Приветственное сообщение\n"
        "/help - Инструкция по использованию\n"
        "/status - Проверка состояния системы\n"
    )
    
    # Add admin commands if user is admin
    if is_admin(user_id):
        welcome_text += (
            "\n⚙️ Команды администратора:\n"
            "/upload_base - Загрузить базу знаний\n"
            "/reset - Очистить память и перезагрузить базу\n"
        )
    
    keyboard = [
        [InlineKeyboardButton("🔍 Найти ответ", callback_data="search_answer")],
        [InlineKeyboardButton("♻️ Перезапустить", callback_data="restart")],
    ]
    
    if is_admin(user_id):
        keyboard.insert(0, [InlineKeyboardButton("📂 Загрузить базу знаний", callback_data="upload_kb")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    logger.info(f"User {user_id} started the bot")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = (
        "📖 Инструкция по использованию:\n\n"
        "1. Загрузите базу знаний (только для администраторов)\n"
        "2. Задавайте вопросы в естественной форме\n"
        "3. Я найду наиболее релевантную информацию\n"
        "4. Используйте кнопки для быстрого доступа к функциям\n\n"
        "Поддерживаемые форматы файлов:\n"
        "• .txt - текстовые файлы\n"
        "• .csv - табличные данные\n"
        "• .json - структурированные данные\n\n"
        "Максимальный размер файла: 20 МБ"
    )
    
    await update.message.reply_text(help_text)
    logger.info(f"User {update.effective_user.id} requested help")

async def upload_base_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /upload_base command"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Эта команда доступна только администраторам.")
        return
    
    await update.message.reply_text(
        "📤 Пожалуйста, загрузите файл базы знаний.\n"
        "Поддерживаемые форматы: .txt, .csv, .json\n"
        "Максимальный размер: 20 МБ"
    )
    logger.info(f"Admin {user_id} initiated knowledge base upload")

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /reset command"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Эта команда доступна только администраторам.")
        return
    
    # Import here to avoid circular imports
    from uploader import KnowledgeBaseManager
    
    kb_manager = KnowledgeBaseManager()
    success = kb_manager.reset_knowledge_base()
    
    if success:
        await update.message.reply_text("✅ Память очищена. База знаний перезагружена.")
        logger.info(f"Admin {user_id} reset the knowledge base")
    else:
        await update.message.reply_text("❌ Ошибка при очистке памяти.")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command"""
    user_id = update.effective_user.id
    
    # Get system info
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Get knowledge base info
    from uploader import KnowledgeBaseManager
    kb_manager = KnowledgeBaseManager()
    kb_info = kb_manager.get_knowledge_base_info()
    
    status_text = (
        "📊 Статус системы:\n\n"
        f"💾 Использование RAM: {memory.percent}%\n"
        f"💿 Использование диска: {disk.percent}%\n"
        f"🔢 Загружено документов: {kb_info['document_count']}\n"
        f"📝 Общее количество чанков: {kb_info['chunk_count']}\n"
        f"📅 Последнее обновление: {kb_info['last_update']}\n"
    )
    
    await update.message.reply_text(status_text)
    logger.info(f"User {user_id} requested status")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular text messages"""
    user_id = update.effective_user.id
    user_message = update.message.text
    
    logger.info(f"User {user_id} sent message: {user_message}")
    
    # Process message with AI engine
    from ai_engine.dp_model import DeepPavlovEngine
    ai_engine = DeepPavlovEngine()
    
    try:
        response = ai_engine.process_query(user_message)
        await update.message.reply_text(response)
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        await update.message.reply_text("❌ Произошла ошибка при обработке запроса. Попробуйте позже.")

async def handle_file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle file uploads"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Загрузка файлов доступна только администраторам.")
        return
    
    document = update.message.document
    file_name = document.file_name
    
    # Check file extension
    file_ext = os.path.splitext(file_name)[1].lower()
    if file_ext not in config.ALLOWED_EXTENSIONS:
        await update.message.reply_text(
            f"❌ Неподдерживаемый формат файла. "
            f"Допустимые форматы: {', '.join(config.ALLOWED_EXTENSIONS)}"
        )
        return
    
    # Check file size
    if document.file_size > config.MAX_FILE_SIZE:
        await update.message.reply_text(f"❌ Размер файла превышает {config.MAX_FILE_SIZE // 1024 // 1024} МБ")
        return
    
    # Download and process file
    from uploader import KnowledgeBaseManager
    
    kb_manager = KnowledgeBaseManager()
    
    try:
        # Download file
        file = await document.get_file()
        file_path = os.path.join(config.KNOWLEDGE_BASE_DIR, file_name)
        await file.download_to_drive(file_path)
        
        # Process file
        await update.message.reply_text("🔄 Обрабатываю файл...")
        result = kb_manager.process_uploaded_file(file_path)
        
        if result["success"]:
            await update.message.reply_text(
                f"✅ Файл успешно обработан!\n"
                f"📄 Документов: {result['documents_processed']}\n"
                f"🔢 Чанков: {result['chunks_created']}"
            )
        else:
            await update.message.reply_text(f"❌ Ошибка при обработке файла: {result['error']}")
            
    except Exception as e:
        logger.error(f"Error processing uploaded file: {e}")
        await update.message.reply_text("❌ Ошибка при загрузке файла.")

async def handle_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button clicks"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    action = query.data
    
    if action == "upload_kb":
        if is_admin(user_id):
            await query.message.reply_text(
                "📤 Пожалуйста, загрузите файл базы знаний.\n"
                "Поддерживаемые форматы: .txt, .csv, .json"
            )
        else:
            await query.edit_message_text("❌ Эта функция доступна только администраторам.")
    
    elif action == "search_answer":
        await query.edit_message_text("💭 Задайте ваш вопрос в виде обычного сообщения.")
    
    elif action == "restart":
        if is_admin(user_id):
            from uploader import KnowledgeBaseManager
            kb_manager = KnowledgeBaseManager()
            kb_manager.reset_knowledge_base()
            await query.edit_message_text("✅ Система перезапущена. Память очищена.")
        else:
            await query.edit_message_text("❌ Эта функция доступна только администраторам.")
