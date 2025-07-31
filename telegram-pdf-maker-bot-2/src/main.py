import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes
)

# Change these relative imports to absolute imports
from src.handlers.image_processing import ImageProcessor
from src.utils.pdf_generator import PDFGenerator

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# States
WAITING_IMAGES, CHOOSING_STYLE, CHOOSING_QUALITY = range(3)

# Constants
IMAGE_DIR = "downloads"
user_data_store = {}

# Initialize directories
os.makedirs(IMAGE_DIR, exist_ok=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_dir = os.path.join(IMAGE_DIR, user_id)
    os.makedirs(user_dir, exist_ok=True)
    
    user_data_store[user_id] = {
        "images": [],
        "style": None,
        "quality": None
    }
    
    await update.message.reply_text(
        "Welcome! Send me images and I'll convert them to PDF.\n"
        "Send /done when you're finished sending images."
    )
    return WAITING_IMAGES

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    photo = update.message.photo[-1]
    
    file = await context.bot.get_file(photo.file_id)
    file_path = os.path.join(IMAGE_DIR, user_id, f"{len(user_data_store[user_id]['images'])}.jpg")
    await file.download_to_drive(file_path)
    
    user_data_store[user_id]["images"].append(file_path)
    await update.message.reply_text(f"Image received! Total: {len(user_data_store[user_id]['images'])}")
    
    return WAITING_IMAGES

async def done_uploading(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Original", callback_data="original")],
        [InlineKeyboardButton("Grayscale", callback_data="grayscale")],
        [InlineKeyboardButton("Black & White", callback_data="black_white")],
        [InlineKeyboardButton("Enhanced", callback_data="enhanced")]
    ]
    
    await update.message.reply_text(
        "Choose image style:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CHOOSING_STYLE

async def select_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    user_data_store[user_id]["style"] = query.data
    
    keyboard = [
        [InlineKeyboardButton("High", callback_data="high")],
        [InlineKeyboardButton("Medium", callback_data="medium")],
        [InlineKeyboardButton("Low", callback_data="low")]
    ]
    
    await query.edit_message_text(
        text="Select PDF quality:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CHOOSING_QUALITY

async def select_quality(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    user_info = user_data_store[user_id]
    user_info["quality"] = query.data
    
    await query.edit_message_text("Generating your PDF...")
    
    pdf_generator = PDFGenerator()
    output_pdf = os.path.join(IMAGE_DIR, f"{user_id}_output.pdf")
    
    try:
        pdf_generator.generate_pdf(
            user_info["images"],
            output_pdf,
            user_info["style"],
            user_info["quality"]
        )
        
        with open(output_pdf, "rb") as pdf_file:
            await context.bot.send_document(
                chat_id=query.message.chat_id,
                document=pdf_file
            )
            
        # Cleanup
        os.remove(output_pdf)
        for img in user_info["images"]:
            os.remove(img)
        os.rmdir(os.path.join(IMAGE_DIR, user_id))
        del user_data_store[user_id]
        
    except Exception as e:
        await query.edit_message_text(f"Error generating PDF: {str(e)}")
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id in user_data_store:
        del user_data_store[user_id]
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(os.getenv('BOT_TOKEN')).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAITING_IMAGES: [
                MessageHandler(filters.PHOTO, handle_image),
                CommandHandler("done", done_uploading)
            ],
            CHOOSING_STYLE: [CallbackQueryHandler(select_style)],
            CHOOSING_QUALITY: [CallbackQueryHandler(select_quality)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    
    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == '__main__':
    main()