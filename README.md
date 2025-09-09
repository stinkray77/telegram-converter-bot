#  telegram-converter-bot 🤖

A powerful Telegram bot that can convert between various file formats including images, documents, videos, and data files.

## Features ✨

- **Image Conversion**: JPG, PNG, PDF, WebP, BMP, GIF, TIFF
- **Document Conversion**: PDF, DOCX, TXT
- **Video Conversion**: MP4, AVI, MOV, MKV, WebM to MP4/GIF/MP3
- **Data Conversion**: CSV, Excel, JSON
- **Easy to Use**: Simple inline keyboard interface
- **Fast Processing**: Efficient file handling with cleanup

## Supported Conversions 📁

### Images
- **From**: JPG, JPEG, PNG, BMP, GIF, TIFF, WebP
- **To**: JPG, PNG, PDF, WebP

### Documents  
- **From**: PDF, DOCX, TXT
- **To**: PDF, TXT, DOCX

### Videos
- **From**: MP4, AVI, MOV, MKV, WebM
- **To**: MP4, GIF, MP3 (audio extraction)

### Data Files
- **From**: CSV, XLSX, JSON
- **To**: CSV, XLSX, JSON

## Setup & Installation 🛠️

### Prerequisites
- Python 3.8+
- A Telegram Bot Token (from [@BotFather](https://t.me/botfather))

### Local Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/telegram-file-converter-bot.git
   cd telegram-file-converter-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   export TELEGRAM_BOT_TOKEN="your_bot_token_here"
   ```
   
   Or create a `.env` file:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   ```

4. **Run the bot**
   ```bash
   python bot.py
   ```

### Docker Installation 🐳

1. **Build the Docker image**
   ```bash
   docker build -t telegram-converter-bot .
   ```

2. **Run the container**
   ```bash
   docker run -e TELEGRAM_BOT_TOKEN="your_token_here" telegram-converter-bot
   ```

### Heroku Deployment 🚀

1. **Create a new Heroku app**
   ```bash
   heroku create your-app-name
   ```

2. **Set environment variables**
   ```bash
   heroku config:set TELEGRAM_BOT_TOKEN="your_token_here"
   ```

3. **Deploy**
   ```bash
   git push heroku main
   ```

## Usage 📱

1. **Start the bot**: Send `/start` to your bot
2. **Upload a file**: Send any supported file to the bot
3. **Choose format**: Select the target format from the buttons
4. **Download**: Receive your converted file

### Available Commands

- `/start` - Initialize the bot
- `/help` - Show help message
- `/formats` - Display all supported formats

## Configuration ⚙️

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token | ✅ Yes |
| `MAX_FILE_SIZE` | Maximum file size in MB (default: 50) | ❌ No |
| `LOG_LEVEL` | Logging level (default: INFO) | ❌ No |

### Advanced Configuration

You can modify the `SUPPORTED_CONVERSIONS` dictionary in `bot.py` to add or remove supported formats.

## File Structure 📂

```
telegram-file-converter-bot/
├── bot.py                 # Main bot application
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── Procfile             # Heroku process file
├── runtime.txt          # Python version for Heroku
├── .env.example         # Environment variables example
├── .gitignore          # Git ignore rules
├── README.md           # This file
└── tests/              # Test files
    ├── __init__.py
    ├── test_converter.py
    └── test_bot.py
```

## Contributing 🤝

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Commit your changes**
   ```bash
   git commit -m 'Add some amazing feature'
   ```
4. **Push to the branch**
   ```bash
   git push origin feature/amazing-feature
   ```
5. **Open a Pull Request**

## Testing 🧪

Run tests with pytest:

```bash
pip install pytest
pytest tests/
```

## Limitations ⚠️

- Maximum file size: 50MB (Telegram limitation)
- Video to GIF conversion limited to first 10 seconds
- Some advanced document formatting may be lost during conversion
- Processing time depends on file size and format complexity

## Troubleshooting 🔧

### Common Issues

1. **Bot doesn't respond**
   - Check if the bot token is correct
   - Ensure the bot is running
   - Verify network connectivity

2. **Conversion fails**
   - Check if the file format is supported
   - Ensure the file isn't corrupted
   - Verify sufficient disk space

3. **Memory issues**
   - Large files may cause memory errors
   - Consider reducing file size before conversion
   - Restart the bot if memory usage is high

### Logs

Check the bot logs for detailed error messages:
```bash
tail -f bot.log
```

## Security 🔒

- Files are processed in temporary directories and automatically cleaned up
- No files are permanently stored on the server
- All processing happens locally/on your server
- Consider implementing rate limiting for production use

## License 📄

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments 🙏

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram Bot API wrapper
- [Pillow](https://pillow.readthedocs.io/) - Image processing
- [PyMuPDF](https://pymupdf.readthedocs.io/) - PDF processing
- [MoviePy](https://zulko.github.io/moviepy/) - Video processing
- [Pandas](https://pandas.pydata.org/) - Data processing

## Support 💬

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/yourusername/telegram-file-converter-bot/issues) page
2. Create a new issue with detailed information
3. Contact: [your-email@example.com](mailto:your-email@example.com)

---

Made with ❤️ by [Your Name](https://github.com/yourusername)