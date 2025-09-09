import os
import logging
from pathlib import Path
import tempfile
from typing import Dict, Any

from dotenv import load_dotenv
load_dotenv()

from telegram import Update, Document
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes
)

# File conversion imports
from PIL import Image
import fitz  # PyMuPDF for PDF operations
from moviepy.editor import VideoFileClip
import pandas as pd
from docx import Document as DocxDocument
import subprocess

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
            'to': ['.jpg', '.png', '.pdf', '.webp']
        },
        'document': {
            'from': ['.pdf', '.docx', '.txt'],
            'to': ['.pdf', '.txt', '.docx']
        },
        'video': {
            'from': ['.mp4', '.avi', '.mov', '.mkv', '.webm'],
            'to': ['.mp4', '.gif', '.mp3']  # mp3 for audio extraction
        },
        'data': {
            'from': ['.csv', '.xlsx', '.json'],
            'to': ['.csv', '.xlsx', '.json']
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
                
                if target_format.lower() == 'pdf':
                    img.save(output_path, 'PDF', resolution=100.0)
                else:
                    img.save(output_path, target_format)
            return True
        except Exception as e:
            logger.error(f"Image conversion error: {e}")
            return False
    
    @staticmethod
    def convert_document(input_path: str, output_path: str, target_format: str) -> bool:
        """Convert document files"""
        try:
            input_ext = Path(input_path).suffix.lower()
            
            if input_ext == '.pdf' and target_format == 'txt':
                # PDF to text
                doc = fitz.open(input_path)
                text = ""
                for page in doc:
                    text += page.get_text()
                doc.close()
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                return True
                
            elif input_ext == '.docx' and target_format == 'txt':
                # DOCX to text
                doc = DocxDocument(input_path)
                text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                return True
                
            elif input_ext == '.txt' and target_format == 'pdf':
                # Text to PDF (using reportlab would be better, but keeping dependencies minimal)
                # This is a simplified conversion
                subprocess.run([
                    'python', '-c',
                    f"""
import fitz
doc = fitz.open()
page = doc.new_page()
with open('{input_path}', 'r', encoding='utf-8') as f:
    text = f.read()
page.insert_text((72, 72), text, fontsize=12)
doc.save('{output_path}')
doc.close()
"""
                ], check=True)
                return True
                
        except Exception as e:
            logger.error(f"Document conversion error: {e}")
            return False
        
        return False
    
    @staticmethod
    def convert_video(input_path: str, output_path: str, target_format: str) -> bool:
        """Convert video files"""
        try:
            if target_format == 'mp3':
                # Extract audio
                clip = VideoFileClip(input_path)
                clip.audio.write_audiofile(output_path)
                clip.close()
            elif target_format == 'gif':
                # Convert to GIF (first 10 seconds to keep size reasonable)
                clip = VideoFileClip(input_path).subclip(0, min(10, VideoFileClip(input_path).duration))
                clip.write_gif(output_path, fps=10)
                clip.close()
            else:
                # Video format conversion
                clip = VideoFileClip(input_path)
                clip.write_videofile(output_path)
                clip.close()
            return True
        except Exception as e:
            logger.error(f"Video conversion error: {e}")
            return False
    
    @staticmethod
    def convert_data(input_path: str, output_path: str, target_format: str) -> bool:
        """Convert data files"""
        try:
            input_ext = Path(input_path).suffix.lower()
            
            if input_ext == '.csv':
                df = pd.read_csv(input_path)
            elif input_ext == '.xlsx':
                df = pd.read_excel(input_path)
            elif input_ext == '.json':
                df = pd.read_json(input_path)
            else:
                return False
            
            if target_format == 'csv':
                df.to_csv(output_path, index=False)
            elif target_format == 'xlsx':
                df.to_excel(output_path, index=False)
            elif target_format == 'json':
                df.to_json(output_path, orient='records', indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Data conversion error: {e}")
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
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a message when the command /start is issued"""
        welcome_message = (
            "🤖 Welcome to File Converter Bot!\n\n"
            "Send me files and I'll help you convert them to different formats.\n"
            "Use /help to see available commands.\n"
            "Use /formats to see supported file types."
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
            "1. Send me a file\n"
            "2. Choose the target format from the buttons\n"
            "3. Wait for conversion to complete\n"
            "4. Download your converted file!\n\n"
            "Supported conversions: Images, Documents, Videos, Data files"
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
    
    MAX_FILE_SIZE = 50 * 1024 * 1024 # 50MB

    async def process_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                          file_obj: Document, file_name: str):
        if file_obj.file_size > MAX_FILE_SIZE:
            await update.message.reply_text("❌ File too large. Maximum size is 50MB.")
            return
        """Process uploaded file and show conversion options"""
        file_extension = Path(file_name).suffix
        file_category = self.converter.get_file_category(file_extension)
        
        if file_category == 'unknown':
            await update.message.reply_text(
                f"❌ Unsupported file type: {file_extension}\n"
                "Use /formats to see supported formats."
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
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
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
            success = await self.convert_file(input_path, output_path, 
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
    
    async def convert_file(self, input_path: str, output_path: str, 
                          category: str, target_format: str) -> bool:
        """Convert file based on category"""
        if category == 'image':
            return self.converter.convert_image(input_path, output_path, target_format)
        elif category == 'document':
            return self.converter.convert_document(input_path, output_path, target_format)
        elif category == 'video':
            return self.converter.convert_video(input_path, output_path, target_format)
        elif category == 'data':
            return self.converter.convert_data(input_path, output_path, target_format)
        return False
    
    def run(self):
        """Start the bot"""
        from telegram.ext import CallbackQueryHandler
        
        # Add callback query handler for conversion buttons
        self.application.add_handler(CallbackQueryHandler(self.handle_conversion, 
                                                         pattern="^convert_"))
        
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