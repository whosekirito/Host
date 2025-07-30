import sqlite3
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

ADMIN_IDS = [7577853954]  # Add admin user IDs

# 🔧 Handle /givesub command
async def give_subscription_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return
    
    try:
        _, user_id, plan, months = update.message.text.strip().split()
        user_id = int(user_id)
        months = int(months)
        
        expiry = datetime.now() + timedelta(days=30 * months)
        conn = sqlite3.connect("bot_hosting.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET subscription_type = ?, subscription_expiry = ? WHERE user_id = ?", (plan, expiry.isoformat(), user_id))
        conn.commit()
        conn.close()

        await update.message.reply_text(f"✅ Subscription updated for user {user_id}.\nPlan: {plan.title()}, Months: {months}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}\n\nFormat: `/givesub USER_ID premium 1`", parse_mode='Markdown')

# 📢 Handle /broadcast command
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    msg = update.message.text.replace("/broadcast", "").strip()
    if not msg:
        await update.message.reply_text("❌ Please provide a message to broadcast.")
        return

    conn = sqlite3.connect("bot_hosting.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    user_ids = cursor.fetchall()
    conn.close()

    success = 0
    fail = 0
    for (user_id,) in user_ids:
        try:
            await context.bot.send_message(chat_id=user_id, text=msg, parse_mode='Markdown')
            success += 1
        except:
            fail += 1

    await update.message.reply_text(f"✅ Broadcast complete.\n🟢 Sent: {success}\n🔴 Failed: {fail}")

# ⚙️ Handle admin panel buttons
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
                   "You can use Markdown formatting.",
            parse_mode='Markdown'
        )
    
    elif data == "admin_stats":
        conn = sqlite3.connect('bot_hosting.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM user_bots')
        total_bots = cursor.fetchone()[0]

        conn.close()

        await query.edit_message_caption(
            caption=f"📊 **Statistics**\n\n"
                    f"👥 Users: {total_users}\n"
                    f"🤖 Bots: {total_bots}",
            parse_mode='Markdown'
    )
