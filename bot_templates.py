
# Bot templates and examples for users

PYTHON_BOT_TEMPLATE = """
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Your bot token here
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    \"\"\"Start command handler\"\"\"
    await update.message.reply_text('Hello! I am your bot.')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    \"\"\"Help command handler\"\"\"
    await update.message.reply_text('Available commands:\\n/start - Start the bot\\n/help - Show this help')

def main():
    \"\"\"Start the bot\"\"\"
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
"""

NODEJS_BOT_TEMPLATE = """
const { Telegraf } = require('telegraf');

// Your bot token here
const BOT_TOKEN = 'YOUR_BOT_TOKEN_HERE';

const bot = new Telegraf(BOT_TOKEN);

// Start command
bot.start((ctx) => {
    ctx.reply('Hello! I am your bot.');
});

// Help command
bot.help((ctx) => {
    ctx.reply('Available commands:\\n/start - Start the bot\\n/help - Show this help');
});

// Launch bot
bot.launch();

// Enable graceful stop
process.once('SIGINT', () => bot.stop('SIGINT'));
process.once('SIGTERM', () => bot.stop('SIGTERM'));
"""

def get_template(bot_type):
    \"\"\"Get bot template based on type\"\"\"
    if bot_type == 'python':
        return PYTHON_BOT_TEMPLATE
    elif bot_type == 'nodejs':
        return NODEJS_BOT_TEMPLATE
    return None
