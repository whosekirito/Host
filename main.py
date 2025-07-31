
import os
import logging
import asyncio
import subprocess
import threading
import time
import shutil
import json
import sqlite3
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ChatMember
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
import zipfile
import tempfile
import signal
import psutil

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = "8202785686:AAHYVCcuL_AyGiZikBE1pw2ldDKuqOYMNsA"
UPLOAD_FOLDER = "uploaded_bots"
RUNNING_BOTS = {}
START_IMAGE = "https://te.legra.ph/file/acc3bbc9896f9daee3915-952021b9936dc43a13.jpg"
SUPPORT_GROUP = "https://t.me/AACBotSupport"
UPDATE_CHANNEL = "https://t.me/Kirito_Bots"
SUPPORT_GROUP_ID = "@AACBotSupport"  # Support group username
UPDATE_CHANNEL_ID = "@Kirito_Bots"  # Update channel username
DATABASE_CHANNEL_ID = -1002702207186  # Database channel for storing files
ADMIN_IDS = [7577853954]  # Add admin user IDs

# Database setup
def init_database():
    conn = sqlite3.connect('bot_hosting.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            subscription_type TEXT DEFAULT 'free',
            subscription_expiry DATETIME,
            bots_deployed INTEGER DEFAULT 0,
            joined_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Bots table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_bots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            bot_name TEXT,
            bot_type TEXT,
            file_path TEXT,
            status TEXT DEFAULT 'stopped',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, bot_name)
        )
    ''')
    
    # Bot creation states
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bot_creation_states (
            user_id INTEGER PRIMARY KEY,
            state TEXT,
            bot_name TEXT,
            main_file_path TEXT,
            requirements_path TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

init_database()

# Database helper functions
def get_user_subscription(user_id):
    conn = sqlite3.connect('bot_hosting.db')
    cursor = conn.cursor()
    cursor.execute('SELECT subscription_type, subscription_expiry, bots_deployed FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        sub_type, expiry, bots_count = result
        if expiry:
            expiry_date = datetime.fromisoformat(expiry)
            if expiry_date < datetime.now():
                return 'free', 0, bots_count
        return sub_type, expiry, bots_count
    return 'free', None, 0

def create_user(user_id, username):
    conn = sqlite3.connect('bot_hosting.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', (user_id, username))
    conn.commit()
    conn.close()

def update_subscription(user_id, sub_type, months=1):
    conn = sqlite3.connect('bot_hosting.db')
    cursor = conn.cursor()
    expiry = datetime.now() + timedelta(days=30*months)
    cursor.execute('UPDATE users SET subscription_type = ?, subscription_expiry = ? WHERE user_id = ?', 
                  (sub_type, expiry.isoformat(), user_id))
    conn.commit()
    conn.close()

def get_user_bots(user_id):
    conn = sqlite3.connect('bot_hosting.db')
    cursor = conn.cursor()
    cursor.execute('SELECT bot_name, bot_type, status FROM user_bots WHERE user_id = ?', (user_id,))
    results = cursor.fetchall()
    conn.close()
    return results

def add_bot_to_db(user_id, bot_name, bot_type, file_path):
    conn = sqlite3.connect('bot_hosting.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO user_bots (user_id, bot_name, bot_type, file_path) VALUES (?, ?, ?, ?)',
                  (user_id, bot_name, bot_type, file_path))
    cursor.execute('UPDATE users SET bots_deployed = bots_deployed + 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def delete_bot_from_db(user_id, bot_name):
    conn = sqlite3.connect('bot_hosting.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM user_bots WHERE user_id = ? AND bot_name = ?', (user_id, bot_name))
    cursor.execute('UPDATE users SET bots_deployed = bots_deployed - 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def set_creation_state(user_id, state, **kwargs):
    conn = sqlite3.connect('bot_hosting.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO bot_creation_states (user_id, state, bot_name, main_file_path, requirements_path) VALUES (?, ?, ?, ?, ?)',
                  (user_id, state, kwargs.get('bot_name'), kwargs.get('main_file_path'), kwargs.get('requirements_path')))
    conn.commit()
    conn.close()

def get_creation_state(user_id):
    conn = sqlite3.connect('bot_hosting.db')
    cursor = conn.cursor()
    cursor.execute('SELECT state, bot_name, main_file_path, requirements_path FROM bot_creation_states WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def clear_creation_state(user_id):
    conn = sqlite3.connect('bot_hosting.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM bot_creation_states WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

# Store files in database channel
async def store_file_in_database(context, file_path, user_id, bot_name, file_type):
    try:
        with open(file_path, 'rb') as file:
            caption = f"**Bot File Backup**\n\n"
            caption += f"👤 User ID: {user_id}\n"
            caption += f"🤖 Bot Name: {bot_name}\n"
            caption += f"📄 File Type: {file_type}\n"
            caption += f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            await context.bot.send_document(
                chat_id=DATABASE_CHANNEL_ID,
                document=file,
                caption=caption,
                parse_mode='Markdown'
            )
            logger.info(f"File stored in database channel: {file_path}")
    except Exception as e:
        logger.error(f"Error storing file in database channel: {e}")

# Force join check
async def check_membership(context, user_id):
    try:
        # Check support group
        try:
            member = await context.bot.get_chat_member(SUPPORT_GROUP_ID, user_id)
            if member.status in ["left", "kicked"]:
                return False
        except Exception as e:
            logger.error(f"Error checking support group membership: {e}")
            return True  # Allow access if API fails
        
        # Check update channel  
        try:
            member = await context.bot.get_chat_member(UPDATE_CHANNEL_ID, user_id)
            if member.status in ["left", "kicked"]:
                return False
        except Exception as e:
            logger.error(f"Error checking channel membership: {e}")
            return True  # Allow access if API fails
        
        return True
    except Exception as e:
        logger.error(f"Error in membership check: {e}")
        return True

class BotManager:
    def __init__(self):
        self.running_bots = {}
        self.bot_logs = {}
    
    def start_bot(self, user_id, bot_name, bot_type, file_path):
        try:
            bot_key = f"{user_id}_{bot_name}"
            
            # Clean and normalize the file path
            if not os.path.isabs(file_path):
                file_path = os.path.abspath(file_path)
            
            # Fix duplicate path issue
            file_path = os.path.normpath(file_path)
            
            if not os.path.exists(file_path):
                logger.error(f"Bot file not found at: {file_path}")
                return False, f"Bot file not found: {file_path}"
            
            if bot_type == "python":
                process = subprocess.Popen(
                    ["python3", file_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    cwd=os.path.dirname(file_path),
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
            elif bot_type == "nodejs":
                process = subprocess.Popen(
                    ["node", file_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    cwd=os.path.dirname(file_path),
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
            
            self.running_bots[bot_key] = {
                'process': process,
                'start_time': datetime.now(),
                'bot_name': bot_name,
                'bot_type': bot_type,
                'user_id': user_id
            }
            
            self.bot_logs[bot_key] = []
            
            # Start log monitoring
            threading.Thread(target=self._monitor_logs, args=(bot_key, process), daemon=True).start()
            
            # Update database
            conn = sqlite3.connect('bot_hosting.db')
            cursor = conn.cursor()
            cursor.execute('UPDATE user_bots SET status = ? WHERE user_id = ? AND bot_name = ?',
                          ('running', user_id, bot_name))
            conn.commit()
            conn.close()
            
            return True, "Bot started successfully"
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            return False, f"Error starting bot: {str(e)}"
    
    def _monitor_logs(self, bot_key, process):
        try:
            for line in iter(process.stdout.readline, ''):
                if bot_key in self.bot_logs:
                    self.bot_logs[bot_key].append(f"{datetime.now().strftime('%H:%M:%S')} - {line.strip()}")
                    # Keep only last 100 log lines
                    if len(self.bot_logs[bot_key]) > 100:
                        self.bot_logs[bot_key] = self.bot_logs[bot_key][-100:]
        except:
            pass
    
    def stop_bot(self, user_id, bot_name):
        bot_key = f"{user_id}_{bot_name}"
        if bot_key in self.running_bots:
            try:
                process = self.running_bots[bot_key]['process']
                process.terminate()
                process.wait(timeout=5)
                del self.running_bots[bot_key]
                
                # Update database
                conn = sqlite3.connect('bot_hosting.db')
                cursor = conn.cursor()
                cursor.execute('UPDATE user_bots SET status = ? WHERE user_id = ? AND bot_name = ?',
                              ('stopped', user_id, bot_name))
                conn.commit()
                conn.close()
                
                return True, "Bot stopped successfully"
            except Exception as e:
                return False, f"Error stopping bot: {str(e)}"
        return False, "Bot not found or already stopped"
    
    def get_bot_logs(self, user_id, bot_name):
        bot_key = f"{user_id}_{bot_name}"
        return self.bot_logs.get(bot_key, ["No logs available"])
    
    def restart_bot(self, user_id, bot_name):
        # Get bot info from database
        conn = sqlite3.connect('bot_hosting.db')
        cursor = conn.cursor()
        cursor.execute('SELECT bot_type, file_path FROM user_bots WHERE user_id = ? AND bot_name = ?',
                      (user_id, bot_name))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return False, "Bot not found"
        
        bot_type, file_path = result
        
        # Stop if running
        self.stop_bot(user_id, bot_name)
        time.sleep(2)
        
        # Start again
        return self.start_bot(user_id, bot_name, bot_type, file_path)

bot_manager = BotManager()

# Auto dependency detection and installation for premium users
def detect_and_install_dependencies(file_path, is_premium=False):
    """Auto detect and install dependencies from Python file"""
    if not is_premium:
        return True, "Auto dependency installation is a premium feature"
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Common libraries and their pip names
        dependency_map = {
            'requests': 'requests',
            'flask': 'flask',
            'django': 'django',
            'numpy': 'numpy',
            'pandas': 'pandas',
            'matplotlib': 'matplotlib',
            'seaborn': 'seaborn',
            'opencv': 'opencv-python',
            'cv2': 'opencv-python',
            'PIL': 'Pillow',
            'telegram': 'python-telegram-bot',
            'discord': 'discord.py',
            'beautifulsoup4': 'beautifulsoup4',
            'bs4': 'beautifulsoup4',
            'selenium': 'selenium',
            'scrapy': 'scrapy',
            'sqlalchemy': 'sqlalchemy',
            'psycopg2': 'psycopg2-binary',
            'mysql': 'mysql-connector-python',
            'redis': 'redis',
            'celery': 'celery',
            'fastapi': 'fastapi',
            'uvicorn': 'uvicorn',
            'aiohttp': 'aiohttp',
            'asyncio': '',  # Built-in
            'json': '',     # Built-in
            'os': '',       # Built-in
            'sys': '',      # Built-in
            'datetime': '', # Built-in
            're': '',       # Built-in
            'time': '',     # Built-in
            'random': '',   # Built-in
            'math': '',     # Built-in
        }
        
        # Find import statements
        import re
        imports = re.findall(r'^(?:from\s+(\w+)|import\s+(\w+))', content, re.MULTILINE)
        detected_deps = set()
        
        for from_import, direct_import in imports:
            module = from_import or direct_import
            if module in dependency_map and dependency_map[module]:
                detected_deps.add(dependency_map[module])
        
        if detected_deps:
            # Install detected dependencies
            deps_list = list(detected_deps)
            try:
                result = subprocess.run(["python3", "-m", "pip", "install"] + deps_list, 
                                       check=True, capture_output=True, text=True)
                return True, f"Auto-installed dependencies: {', '.join(deps_list)}"
            except subprocess.CalledProcessError as e:
                return False, f"Failed to auto-install dependencies: {e.stderr}"
        else:
            return True, "No additional dependencies detected"
            
    except Exception as e:
        return False, f"Error in auto dependency detection: {str(e)}"

# Install requirements
def install_requirements(requirements_path):
    try:
        # First try UPM (Universal Package Manager) which is recommended for Replit
        try:
            result = subprocess.run(["upm", "add", "-r", requirements_path], 
                                   check=True, capture_output=True, text=True)
            return True, "Requirements installed successfully with UPM"
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to python -m pip if UPM fails
            result = subprocess.run(["python3", "-m", "pip", "install", "-r", requirements_path], 
                                   check=True, capture_output=True, text=True)
            return True, "Requirements installed successfully with pip"
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        return False, f"Failed to install requirements: {error_msg}"
    except Exception as e:
        return False, f"Error installing requirements: {str(e)}"

# Telegram Bot Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if the command is used in private chat only
    if update.message.chat.type != 'private':
        await update.message.reply_text(
            "❌ **Bot Restriction**\n\n"
            "This bot only works in private chats for security reasons.\n"
            "Please start the bot in a private message.",
            parse_mode='Markdown'
        )
        return
    
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    # Check membership
    if not await check_membership(context, user_id):
        keyboard = [
            [InlineKeyboardButton("Join Support Group", url=SUPPORT_GROUP)],
            [InlineKeyboardButton("Join Update Channel", url=UPDATE_CHANNEL)],
            [InlineKeyboardButton("✅ I Joined Both", callback_data="check_join")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_photo(
            photo=START_IMAGE,
            caption="🚫 **Access Denied**\n\n"
                   "You must join both our Support Group and Update Channel to use this bot.\n\n"
                   "After joining both, click 'I Joined Both' button.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return
    
    create_user(user_id, username)
    sub_type, expiry, bots_count = get_user_subscription(user_id)
    
    keyboard = [
        [InlineKeyboardButton("🤖 Create New Bot", callback_data="create_bot")],
        [InlineKeyboardButton("📱 My Bots", callback_data="mybots"), 
         InlineKeyboardButton("💳 Subscription", callback_data="subscription")],
        [InlineKeyboardButton("📊 Dashboard", callback_data="dashboard"),
         InlineKeyboardButton("ℹ️ Help", callback_data="help")],
        [InlineKeyboardButton("💬 Support", url=SUPPORT_GROUP),
         InlineKeyboardButton("📢 Updates", url=UPDATE_CHANNEL)]
    ]
    
    if user_id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Welcome message for all users (removed admin-only restriction)
    welcome_text = f"""🤖 **Kɪʀɪᴛᴏ Hᴏsᴛ Bᴏᴛ**

✨ **ᴡᴇʟᴄᴏᴍᴇ {username}!** ✨

🚀 **ғᴇᴀᴛᴜʀᴇs:**
• Python & Node.js bots
• 24/7 hosting with auto-restart
• Real-time logs & monitoring
{f'• Auto dependency installation' if sub_type == 'premium' else ''}

📋 **ʏᴏᴜʀ ᴘʟᴀɴ:** {sub_type.title()} - {'Unlimited' if user_id in ADMIN_IDS else ('15' if sub_type == 'premium' else '1')} bots
🤖 **Bots Deployed:** {bots_count}

🎯 **ǫᴜɪᴄᴋ sᴛᴀʀᴛ:**
1. Click "Create New Bot"
2. Upload files and start hosting!"""
    
    await update.message.reply_photo(
        photo=START_IMAGE,
        caption=welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "check_join":
        if await check_membership(context, user_id):
            await query.edit_message_caption(
                caption="✅ **Welcome!** You can now use the bot.\n\nSend /start to begin!",
                parse_mode='Markdown'
            )
        else:
            await query.answer("❌ You haven't joined both channels yet!", show_alert=True)
        return
    
    # Check membership for all other actions
    if not await check_membership(context, user_id):
        await query.answer("❌ Please join both channels first!", show_alert=True)
        return
    
    if data == "create_bot":
        sub_type, expiry, bots_count = get_user_subscription(user_id)
       
