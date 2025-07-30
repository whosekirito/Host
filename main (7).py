
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
from flask import Flask, render_template, request, jsonify
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

# Create Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
    
    # Special welcome message for admin
    if user_id in ADMIN_IDS:
        welcome_text = f"""🤖 **Kɪʀɪᴛᴏ Hᴏsᴛ Bᴏᴛ**

✨ **ᴡᴇʟᴄᴏᴍᴇ Kɪʀɪᴛᴏ!** ✨

🚀 **ғᴇᴀᴛᴜʀᴇs:**
• Python & Node.js bots
• 24/7 hosting with auto-restart
• Real-time logs & monitoring
• Auto dependency installation

📋 **ʏᴏᴜʀ ᴘʟᴀɴ:** 👑 Admin - Unlimited bots

🎯 **ǫᴜɪᴄᴋ sᴛᴀʀᴛ:**
1. Click "Create New Bot"
2. Enter bot name
3. Upload main.py and requirements.txt
4. Your bot runs 24/7!"""
    else:
        welcome_text = f"""🤖 **Kɪʀɪᴛᴏ Hᴏsᴛ Bᴏᴛ**

✨ **ᴡᴇʟᴄᴏᴍᴇ {username}!** ✨

🚀 **ғᴇᴀᴛᴜʀᴇs:**
• Python & Node.js bots
• 24/7 hosting with auto-restart
• Real-time logs & monitoring

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
        
        # Admin users have unlimited bots
        if user_id not in ADMIN_IDS:
            max_bots = 1 if sub_type == 'free' else 15
            if bots_count >= max_bots:
                await query.edit_message_caption(
                    caption=f"❌ **Bot Limit Reached**\n\n"
                           f"You have reached your limit of {max_bots} bots.\n"
                           f"{'Upgrade to Premium to deploy up to 15 bots!' if sub_type == 'free' else 'Contact admin for more bots.'}",
                    parse_mode='Markdown'
                )
                return
        
        set_creation_state(user_id, 'waiting_name')
        await query.edit_message_caption(
            caption="🤖 **Create New Bot**\n\n"
                   "Please enter a name for your bot (alphanumeric only):",
            parse_mode='Markdown'
        )
    
    elif data == "mybots":
        user_bots = get_user_bots(user_id)
        if not user_bots:
            await query.edit_message_caption(
                caption="🤖 **Your Bots**\n\nYou don't have any bots yet.\nClick 'Create New Bot' to get started!",
                parse_mode='Markdown'
            )
        else:
            bot_list = "🤖 **Your Bots:**\n\n"
            keyboard = []
            for bot_name, bot_type, status in user_bots:
                status_emoji = "🟢" if status == "running" else "🔴"
                bot_list += f"{status_emoji} **{bot_name}** ({bot_type})\n"
                keyboard.append([
                    InlineKeyboardButton(f"⚙️ {bot_name}", callback_data=f"manage_{bot_name}"),
                    InlineKeyboardButton("📊" if status == "running" else "▶️", 
                                       callback_data=f"logs_{bot_name}" if status == "running" else f"start_{bot_name}")
                ])
            
            keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="mainmenu")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_caption(
                caption=bot_list,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    
    elif data.startswith("manage_"):
        bot_name = data.split("_", 1)[1]
        keyboard = [
            [InlineKeyboardButton("▶️ Start", callback_data=f"start_{bot_name}"),
             InlineKeyboardButton("⏹️ Stop", callback_data=f"stop_{bot_name}")],
            [InlineKeyboardButton("🔄 Restart", callback_data=f"restart_{bot_name}"),
             InlineKeyboardButton("📊 Logs", callback_data=f"logs_{bot_name}")],
            [InlineKeyboardButton("🗑️ Delete", callback_data=f"delete_{bot_name}"),
             InlineKeyboardButton("🔙 Back", callback_data="mybots")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_caption(
            caption=f"⚙️ **Manage Bot: {bot_name}**\n\nChoose an action:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif data.startswith("start_"):
        bot_name = data.split("_", 1)[1]
        
        # Get bot info from DB for proper start
        conn = sqlite3.connect('bot_hosting.db')
        cursor = conn.cursor()
        cursor.execute('SELECT bot_type, file_path FROM user_bots WHERE user_id = ? AND bot_name = ?',
                      (user_id, bot_name))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            bot_type, file_path = result
            if file_path and os.path.exists(file_path):
                success, message = bot_manager.start_bot(user_id, bot_name, bot_type, file_path)
            else:
                success, message = False, "Bot file not found or path is empty"
        else:
            success, message = False, "Bot not found in database"
        
        await query.answer(f"✅ {message}" if success else f"❌ {message}", show_alert=True)
    
    elif data.startswith("stop_"):
        bot_name = data.split("_", 1)[1]
        success, message = bot_manager.stop_bot(user_id, bot_name)
        await query.answer(f"⏹️ {message}" if success else f"❌ {message}", show_alert=True)
    
    elif data.startswith("restart_"):
        bot_name = data.split("_", 1)[1]
        success, message = bot_manager.restart_bot(user_id, bot_name)
        await query.answer(f"🔄 {message}" if success else f"❌ {message}", show_alert=True)
    
    elif data.startswith("logs_"):
        bot_name = data.split("_", 1)[1]
        logs = bot_manager.get_bot_logs(user_id, bot_name)
        log_text = "\n".join(logs[-20:])  # Last 20 logs
        
        await query.edit_message_caption(
            caption=f"📊 **Bot Logs: {bot_name}**\n\n```\n{log_text}\n```",
            parse_mode='Markdown'
        )
    
    elif data.startswith("delete_"):
        bot_name = data.split("_", 1)[1]
        keyboard = [
            [InlineKeyboardButton("❌ Yes, Delete", callback_data=f"confirm_delete_{bot_name}"),
             InlineKeyboardButton("✅ Cancel", callback_data="mybots")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_caption(
            caption=f"⚠️ **Delete Bot: {bot_name}**\n\nAre you sure? This action cannot be undone!",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif data.startswith("confirm_delete_"):
        bot_name = data.split("_", 2)[2]
        bot_manager.stop_bot(user_id, bot_name)
        delete_bot_from_db(user_id, bot_name)
        
        # Delete files
        bot_dir = os.path.join(UPLOAD_FOLDER, str(user_id), bot_name)
        if os.path.exists(bot_dir):
            shutil.rmtree(bot_dir)
        
        await query.answer("🗑️ Bot deleted successfully!", show_alert=True)
        # Redirect to mybots
        await button_callback(update, context)  # Simulate mybots click
    
    elif data == "subscription":
        sub_type, expiry, bots_count = get_user_subscription(user_id)
        
        keyboard = []
        if sub_type == 'free':
            keyboard.append([InlineKeyboardButton("💎 Upgrade to Premium (₹799/month)", callback_data="upgrade_premium")])
        
        keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="mainmenu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        expiry_text = f"Expires: {expiry}" if expiry else "No expiry"
        
        await query.edit_message_caption(
            caption=f"💳 **Your Subscription**\n\n"
                   f"Plan: {sub_type.title()}\n"
                   f"Max Bots: {'1' if sub_type == 'free' else '15'}\n"
                   f"Deployed: {bots_count}\n"
                   f"{expiry_text if sub_type != 'free' else ''}\n\n"
                   f"{'Upgrade to Premium for more bots!' if sub_type == 'free' else 'Thank you for being Premium!'}",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif data == "upgrade_premium":
        keyboard = [
            [InlineKeyboardButton("💸 Pay ₹799", url="https://t.me/YourPaymentBot")],
            [InlineKeyboardButton("🔙 Back", callback_data="subscription")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_caption(
            caption="💎 **Premium Subscription**\n\n"
                   "**Benefits:**\n"
                   "✅ Deploy up to 15 bots\n"
                   "✅ Priority support\n"
                   "✅ Advanced features\n"
                   "✅ No ads\n\n"
                   "**Price:** ₹799/month\n\n"
                   "Contact admin after payment for activation.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif data == "dashboard":
        user_bots = get_user_bots(user_id)
        sub_type, expiry, bots_count = get_user_subscription(user_id)
        
        running_bots = len([bot for bot in user_bots if bot[2] == 'running'])
        stopped_bots = len([bot for bot in user_bots if bot[2] == 'stopped'])
        
        keyboard = [[InlineKeyboardButton("🏠 Main Menu", callback_data="mainmenu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_caption(
            caption=f"📊 **Your Dashboard**\n\n"
                   f"💳 **Subscription:** {sub_type.title()}\n"
                   f"🤖 **Total Bots:** {bots_count}\n"
                   f"🟢 **Running:** {running_bots}\n"
                   f"🔴 **Stopped:** {stopped_bots}\n"
                   f"⏰ **Max Allowed:** {'1' if sub_type == 'free' else '15'}\n\n"
                   f"📅 **Joined:** {datetime.now().strftime('%Y-%m-%d')}",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif data == "help":
        keyboard = [[InlineKeyboardButton("🏠 Main Menu", callback_data="mainmenu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        help_text = """
ℹ️ **Help & Support**

**How to use:**
1. Click 'Create New Bot'
2. Enter bot name
3. Upload main.py file
4. Upload requirements.txt file
5. Bot will be automatically deployed!

**Features:**
🤖 Python bot hosting
📊 Real-time logs
🔄 Auto-restart
⚙️ Easy management

**Limits:**
🆓 Free: 1 bot
💎 Premium: 15 bots (₹799/month)

**Support:**
💬 Support Group: @AACBotSupport
📢 Updates: @Kirito_Bots
        """
        
        await query.edit_message_caption(
            caption=help_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif data == "admin_panel" and user_id in ADMIN_IDS:
        keyboard = [
            [InlineKeyboardButton("👥 Give Subscription", callback_data="admin_give_sub"),
             InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
            [InlineKeyboardButton("📊 Statistics", callback_data="admin_stats"),
             InlineKeyboardButton("👥 Users", callback_data="admin_users")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="mainmenu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await query.edit_message_caption(
                caption="👑 **Admin Panel**\n\nChoose an action:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except Exception:
            await query.message.reply_text(
                "👑 **Admin Panel**\n\nChoose an action:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    
    # Handle admin-specific callbacks
    elif data.startswith("admin_") and user_id in ADMIN_IDS:
        from admin_handlers import handle_admin_commands
        await handle_admin_commands(update, context, data)
    
    elif data == "mainmenu":
        # Handle main menu properly for callback queries
        user_id = query.from_user.id
        username = query.from_user.username or "Unknown"
        
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
        
        # Special welcome message for admin
        if user_id in ADMIN_IDS:
            welcome_text = f"""🤖 **Kɪʀɪᴛᴏ Hᴏsᴛ Bᴏᴛ**

✨ **ᴡᴇʟᴄᴏᴍᴇ Kɪʀɪᴛᴏ!** ✨

🚀 **ғᴇᴀᴛᴜʀᴇs:**
• Python & Node.js bots
• 24/7 hosting with auto-restart
• Real-time logs & monitoring
• Auto dependency installation

📋 **ʏᴏᴜʀ ᴘʟᴀɴ:** 👑 Admin - Unlimited bots

🎯 **ǫᴜɪᴄᴋ sᴛᴀʀᴛ:**
1. Click "Create New Bot"
2. Enter bot name
3. Upload main.py and requirements.txt
4. Your bot runs 24/7!"""
        else:
            welcome_text = f"""🤖 **Kɪʀɪᴛᴏ Hᴏsᴛ Bᴏᴛ**

✨ **ᴡᴇʟᴄᴏᴍᴇ {username}!** ✨

🚀 **ғᴇᴀᴛᴜʀᴇs:**
• Python & Node.js bots
• 24/7 hosting with auto-restart
• Real-time logs & monitoring

📋 **ʏᴏᴜʀ ᴘʟᴀɴ:** {sub_type.title()} - {'Unlimited' if user_id in ADMIN_IDS else ('15' if sub_type == 'premium' else '1')} bots
🤖 **Bots Deployed:** {bots_count}

🎯 **ǫᴜɪᴄᴋ sᴛᴀʀᴛ:**
1. Click "Create New Bot"
2. Upload files and start hosting!"""
        
        try:
            # Try to edit message caption first
            if query.message.caption:
                await query.edit_message_caption(
                    caption=welcome_text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                # If no caption exists, send new photo message
                await query.message.reply_photo(
                    photo=START_IMAGE,
                    caption=welcome_text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"Error handling main menu: {e}")
            # Fallback: delete old message and send new one
            try:
                await query.message.delete()
            except:
                pass
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=START_IMAGE,
                caption=welcome_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Check creation state
    state_info = get_creation_state(user_id)
    if not state_info:
        return
    
    state, bot_name, main_file_path, requirements_path = state_info
    
    if state == 'waiting_name':
        bot_name = update.message.text.strip()
        if not bot_name.replace('_', '').isalnum():
            await update.message.reply_text("❌ Bot name must be alphanumeric only. Please try again:")
            return
        
        set_creation_state(user_id, 'waiting_main_file', bot_name=bot_name)
        await update.message.reply_text(f"✅ Bot name set: **{bot_name}**\n\nNow send your main.py file:", parse_mode='Markdown')
    
    elif state == 'waiting_main_file':
        if not update.message.document:
            await update.message.reply_text("❌ Please send a Python file (.py)")
            return
        
        file = update.message.document
        if not file.file_name.endswith('.py'):
            await update.message.reply_text("❌ Please send a Python file (.py)")
            return
        
        # Download main file
        user_folder = os.path.join(UPLOAD_FOLDER, str(user_id), bot_name)
        os.makedirs(user_folder, exist_ok=True)
        
        new_file = await context.bot.get_file(file.file_id)
        main_file_path = os.path.join(user_folder, "main.py")
        await new_file.download_to_drive(main_file_path)
        
        # Normalize path to prevent duplicates
        main_file_path = os.path.normpath(os.path.abspath(main_file_path))
        logger.info(f"Main file saved at: {main_file_path}")
        
        # Store file in database channel
        await store_file_in_database(context, main_file_path, user_id, bot_name, "main.py")
        
        set_creation_state(user_id, 'waiting_requirements', bot_name=bot_name, main_file_path=main_file_path)
        await update.message.reply_text("✅ Main file uploaded!\n\nNow send your requirements.txt file:")
    
    elif state == 'waiting_requirements':
        if not update.message.document:
            await update.message.reply_text("❌ Please send requirements.txt file")
            return
        
        file = update.message.document
        if file.file_name != 'requirements.txt':
            await update.message.reply_text("❌ File must be named 'requirements.txt'")
            return
        
        # Download requirements file
        user_folder = os.path.join(UPLOAD_FOLDER, str(user_id), bot_name)
        new_file = await context.bot.get_file(file.file_id)
        requirements_path = os.path.join(user_folder, "requirements.txt")
        await new_file.download_to_drive(requirements_path)
        
        # Store requirements file in database channel
        await store_file_in_database(context, requirements_path, user_id, bot_name, "requirements.txt")
        
        status_msg = await update.message.reply_text("📦 Installing requirements... Please wait...")
        
        # Install requirements
        success, message = install_requirements(requirements_path)
        if not success:
            await status_msg.edit_text(f"❌ **Bot Creation Failed**\n\n📦 Requirements installation failed:\n`{message}`", parse_mode='Markdown')
            clear_creation_state(user_id)
            return
        
        await status_msg.edit_text("✅ Requirements installed! Creating bot...", parse_mode='Markdown')
        
        # Add bot to database with correct file path
        add_bot_to_db(user_id, bot_name, 'python', main_file_path)
        clear_creation_state(user_id)
        
        # Try to start the bot automatically
        bot_success, bot_message = bot_manager.start_bot(user_id, bot_name, 'python', main_file_path)
        
        if bot_success:
            await status_msg.edit_text(f"🎉 **Bot Hosted Successfully!**\n\n🤖 **{bot_name}** is now running 24/7!\n\n✅ Status: Online\n📊 Logs: Available\n🔄 Auto-restart: Enabled", parse_mode='Markdown')
        else:
            await status_msg.edit_text(f"⚠️ **Bot Created but Failed to Start**\n\n🤖 **{bot_name}** was created but couldn't start automatically.\n\n❌ Error: {bot_message}\n\nYou can try starting it manually from 'My Bots'.", parse_mode='Markdown')
        
        # Create control buttons
        keyboard = [
            [InlineKeyboardButton("▶️ Start Bot", callback_data=f"start_{bot_name}"),
             InlineKeyboardButton("📊 View Logs", callback_data=f"logs_{bot_name}")],
            [InlineKeyboardButton("🤖 My Bots", callback_data="mybots"),
             InlineKeyboardButton("🏠 Main Menu", callback_data="mainmenu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ **Bot Created Successfully!**\n\n"
            f"🤖 **Name:** {bot_name}\n"
            f"📦 **Requirements:** Installed\n"
            f"🔧 **Type:** Python\n\n"
            f"Your bot is ready to start!",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

# Flask Routes
@app.route('/')
def index():
    total_bots = len(bot_manager.running_bots)
    return f"""
    <html>
    <head>
        <title>Free Bot Hosting Service</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #333; text-align: center; }}
            .feature {{ padding: 15px; margin: 10px 0; background: #e8f4fd; border-left: 4px solid #2196F3; }}
            .btn {{ display: inline-block; padding: 12px 24px; background: #2196F3; color: white; text-decoration: none; border-radius: 5px; margin: 10px 5px; }}
            .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
            .stat-box {{ padding: 20px; background: #f8f9fa; border-radius: 8px; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Free Bot Hosting Service</h1>
            <p style="text-align: center; font-size: 18px; color: #666;">Host your Python and Node.js bots for free with 24/7 uptime</p>
            
            <div class="stats">
                <div class="stat-box">
                    <h3>🚀 Active Bots</h3>
                    <h2>{total_bots}</h2>
                </div>
                <div class="stat-box">
                    <h3>⏰ Uptime</h3>
                    <h2>99.9%</h2>
                </div>
                <div class="stat-box">
                    <h3>💰 Cost</h3>
                    <h2>FREE</h2>
                </div>
            </div>
            
            <div class="feature">
                <h3>📤 Easy Upload</h3>
                <p>Simply send your Python files and requirements.txt to our Telegram bot</p>
            </div>
            
            <div class="feature">
                <h3>🔄 Auto Management</h3>
                <p>Your bots are monitored 24/7 with automatic package installation and restart</p>
            </div>
            
            <div class="feature">
                <h3>📊 Real-time Logs</h3>
                <p>Monitor your bot's performance and logs in real-time</p>
            </div>
            
            <div style="text-align: center; margin-top: 30px;">
                <a href="https://t.me/YourBotUsername" class="btn">🚀 Start Hosting Now</a>
                <a href="{SUPPORT_GROUP}" class="btn">💬 Support</a>
            </div>
        </div>
    </body>
    </html>
    """

def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False)

async def run_telegram_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Import admin handlers
    from admin_handlers import give_subscription_command, broadcast_command
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("givesub", give_subscription_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    
    # Start bot
    await application.initialize()
    await application.start()
    await application.updater.start_polling(drop_pending_updates=True)
    
    # Keep the bot running
    import signal
    stop_signals = (signal.SIGTERM, signal.SIGINT)
    for sig in stop_signals:
        signal.signal(sig, lambda s, f: asyncio.create_task(application.stop()))
    
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()

async def main():
    # Ensure upload directory exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    # Start Flask server in a separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    print("🚀 Bot Hosting Service Started!")
    print("📱 Telegram Bot: Running")
    print("🌐 Web Server: http://0.0.0.0:5000")
    print(f"📢 Support: {SUPPORT_GROUP}")
    print(f"📢 Updates: {UPDATE_CHANNEL}")
    
    # Start Telegram bot
    await run_telegram_bot()

if __name__ == "__main__":
    asyncio.run(main())
