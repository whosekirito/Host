
import sqlite3
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

ADMIN_IDS = [7577853954]  # Add admin user IDs

# Admin functions
async def handle_admin_commands(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    user_id = update.effective_user.id
    query = update.callback_query
    
    if user_id not in ADMIN_IDS:
        await query.answer("❌ Access denied!", show_alert=True)
        return
    
    if data == "admin_give_sub":
        await query.edit_message_caption(
            caption="👥 **Give Subscription**\n\n"
                   "Send user ID and subscription type:\n"
                   "Format: `/givesub USER_ID premium 1`\n"
                   "(USER_ID premium MONTHS)",
            parse_mode='Markdown'
        )
    
    elif data == "admin_broadcast":
        await query.edit_message_caption(
            caption="📢 **Broadcast Message**\n\n"
                   "Send your broadcast message with format:\n"
                   "`/broadcast Your message here`\n\n"
                   "You can use Markdown formatting and inline buttons.",
            parse_mode='Markdown'
        )
    
    elif data == "admin_stats":
        # Get statistics
        conn = sqlite3.connect('bot_hosting.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]

