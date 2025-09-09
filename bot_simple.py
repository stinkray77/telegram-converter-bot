import os
import logging
from pathlib import Path
import tempfile
from typing import Dict, Any

from dotenv import load_dotenv
load_dotenv()

from telegram import Update, Document, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes,
    CallbackQueryHandler
)

# File conversion imports
from PIL import Image

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class FileConverter:
    """Handles file conversion operations"""
    
    SUPPORTED_CONVERSIONS = {
        'image': {
            'from': ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'],
            'to': ['.jpg', '.png', '.webp']
        }
    }
    
    @staticmethod
    def get_file_category(extension: str) -> str:
        """Determine the category of a file based on its extension"""
        for category, formats in FileConverter.SUPPORTED_CONVERSIONS.items():
            if extension.lower() in formats['from']:
                return category
        return 'unknown'
    
    @staticmethod
    def convert_image(input_path: str, output_path: str, target_format: str) -> bool:
        """Convert image files"""
        try:
            with Image.open(input_path) as img:
                # Handle transparency for formats that don't support it
                if target_format.upper() in ['JPEG', 'JPG'] and img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                
                img.save(output_path, target_format.upper())
            return True
        except Exception as e:
            logger.error(f"Image conversion error: {e}")
            return False

class TelegramBot:
    def __init__(self, token: str):
        self.application = Application.builder().token(token).build()
        self.converter = FileConverter()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup command and message handlers"""
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("formats", self.show_formats))
        self.application.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))
        self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
        self.application.add_handler(CallbackQueryHandler(self.handle_conversion, pattern="^convert_"))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a message when the command /start is issued"""
        welcome_message = (
            "🤖 Welcome to File Converter Bot!\n\n"
            "Send me image files and I'll help you convert them to different formats.\n"
            "Use /help to see available commands.\n"
            "Use /formats to see supported file types.\n\n"
            "📸 Currently supporting: JPG, PNG, WebP, BMP, GIF, TIFF"
        )
        await update.message.reply_text(welcome_message)
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send help message"""
        help_message = (
            "📋 Available Commands:\n\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "/formats - Show supported file formats\n\n"
            "📁 How to use:\n"
            "1. Send me an image file\n"
            "2. Choose the target format from the buttons\n"
            "3. Wait for conversion to complete\n"
            "4. Download your converted file!\n\n"
            "🎯 Currently supporting image conversions only"
        )
        await update.message.reply_text(help_message)
    
    async def show_formats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show supported file formats"""
        formats_message = "📋 Supported File Formats:\n\n"
        
        for category, formats in self.converter.SUPPORTED_CONVERSIONS.items():
            formats_message += f"🔸 {category.title()}:\n"
            formats_message += f"   From: {', '.join(formats['from'])}\n"
            formats_message += f"   To: {', '.join(formats['to'])}\n\n"
        
        await update.message.reply_text(formats_message)
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle document uploads"""
        document = update.message.document
        await self.process_file(update, context, document, document.file_name)
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle photo uploads"""
        photo = update.message.photo[-1]  # Get highest resolution
        file_name = f"image_{photo.file_id}.jpg"
        await self.process_file(update, context, photo, file_name)
    
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

    async def process_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                          file_obj: Document, file_name: str):
        if file_obj.file_size > self.MAX_FILE_SIZE:
            await update.message.reply_text("❌ File too large. Maximum size is 50MB.")
            return
        
        """Process uploaded file and show conversion options"""
        file_extension = Path(file_name).suffix
        file_category = self.converter.get_file_category(file_extension)
        
        if file_category == 'unknown':
            await update.message.reply_text(
                f"❌ Unsupported file type: {file_extension}\n"
                "Use /formats to see supported formats.\n\n"
                "🎯 Currently only image files are supported."
            )
            return
        
        # Store file info in user context
        context.user_data['current_file'] = {
            'file_obj': file_obj,
            'file_name': file_name,
            'category': file_category
        }
        
        # Show conversion options
        available_formats = self.converter.SUPPORTED_CONVERSIONS[file_category]['to']
        current_format = file_extension.lower()
        
        # Remove current format from options
        conversion_options = [fmt for fmt in available_formats if fmt != current_format]
        
        if not conversion_options:
            await update.message.reply_text(
                "❌ No conversion options available for this file."
            )
            return
        
        # Create inline keyboard with format options
        keyboard = []
        for fmt in conversion_options:
            callback_data = f"convert_{fmt[1:]}"  # Remove the dot
            keyboard.append([InlineKeyboardButton(f"Convert to {fmt.upper()}", 
                                                callback_data=callback_data)])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"📁 File received: {file_name}\n"
            f"🔸 Type: {file_category.title()}\n"
            f"📊 Size: {file_obj.file_size / 1024:.1f} KB\n\n"
            "Choose conversion format:",
            reply_markup=reply_markup
        )
    
    async def handle_conversion(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle conversion button clicks"""
        query = update.callback_query
        await query.answer()
        
        if 'current_file' not in context.user_data:
            await query.edit_message_text("❌ No file to convert. Please upload a file first.")
            return
        
        target_format = query.data.replace('convert_', '')
        file_info = context.user_data['current_file']
        
        await query.edit_message_text("🔄 Converting file, please wait...")
        
        try:
            # Download the file
            file_obj = file_info['file_obj']
            temp_dir = tempfile.mkdtemp()
            input_path = os.path.join(temp_dir, file_info['file_name'])
            
            file = await context.bot.get_file(file_obj.file_id)
            await file.download_to_drive(input_path)
            
            # Prepare output file
            input_name = Path(file_info['file_name']).stem
            output_filename = f"{input_name}.{target_format}"
            output_path = os.path.join(temp_dir, output_filename)
            
            # Perform conversion
            success = self.convert_file(input_path, output_path, 
                                      file_info['category'], target_format)
            
            if success and os.path.exists(output_path):
                # Send converted file
                with open(output_path, 'rb') as converted_file:
                    await context.bot.send_document(
                        chat_id=query.message.chat_id,
                        document=converted_file,
                        filename=output_filename,
                        caption=f"✅ Converted to {target_format.upper()}"
                    )
                await query.edit_message_text("✅ Conversion completed successfully!")
            else:
                await query.edit_message_text("❌ Conversion failed. Please try again.")
            
            # Cleanup
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            
        except Exception as e:
            logger.error(f"Conversion error: {e}")
            await query.edit_message_text("❌ An error occurred during conversion.")
    
    def convert_file(self, input_path: str, output_path: str, 
                    category: str, target_format: str) -> bool:
        """Convert file based on category"""
        if category == 'image':
            return self.converter.convert_image(input_path, output_path, target_format)
        return False
    
    def run(self):
        """Start the bot"""        
        logger.info("Starting File Converter Bot...")
        self.application.run_polling()

def main():
    # Get bot token from environment variable
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        logger.error("Please set TELEGRAM_BOT_TOKEN environment variable")
        return
    
    bot = TelegramBot(token)
    bot.run()

if __name__ == '__main__':
    main()
