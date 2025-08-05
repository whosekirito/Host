# Applying the provided changes to fix admin panel message editing errors.
import sqlite3
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

BOT_TOKEN = "8202785686:AAFjRhkDXJyvnJk1qsdF6PJK_xgZhoShUjw" # Replace with your bot token

ADMIN_IDS = [7577853954]  # Add admin user IDs

# 🔧 Handle /givesub command
async def give_subscription_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    try:
        parts = update.message.text.strip().split()
        if len(parts) != 4:
            await update.message.reply_text(f"❌ Invalid format.\n\nCorrect format: `/givesub USER_ID premium 1`", parse_mode='Markdown')
            return

        _, user_id, plan, months = parts
        user_id = int(user_id)
        months = int(months)

        # Create user if doesn't exist
        conn = sqlite3.connect("bot_hosting.db")
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', (user_id, "Unknown"))

        expiry = datetime.now() + timedelta(days=30 * months)
        cursor.execute("UPDATE users SET subscription_type = ?, subscription_expiry = ? WHERE user_id = ?", (plan, expiry.isoformat(), user_id))
        conn.commit()
        conn.close()

        await update.message.reply_text(f"✅ Subscription updated for user {user_id}.\nPlan: {plan.title()}, Months: {months}")
    except ValueError:
        await update.message.reply_text(f"❌ Invalid user ID or months value.\n\nFormat: `/givesub USER_ID premium 1`", parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}\n\nFormat: `/givesub USER_ID premium 1`", parse_mode='Markdown')

# 📢 Handle /broadcast command
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    msg = update.message.text.replace("/broadcast", "").strip()
    if not msg:
        await update.message.reply_text("❌ Please provide a message to broadcast.\n\nFormat: `/broadcast Your message here`", parse_mode='Markdown')
        return

    conn = sqlite3.connect("bot_hosting.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    user_ids = cursor.fetchall()
    conn.close()

    success = 0
    fail = 0
    status_msg = await update.message.reply_text(f"📢 Broadcasting to {len(user_ids)} users...")

    for (user_id,) in user_ids:
        try:
            await context.bot.send_message(chat_id=user_id, text=msg, parse_mode='Markdown')
            success += 1
        except Exception as e:
            fail += 1

    await status_msg.edit_text(f"✅ Broadcast complete.\n🟢 Sent: {success}\n🔴 Failed: {fail}")

# ⚙️ Handle admin panel buttons
async def handle_admin_commands(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    user_id = update.effective_user.id
    query = update.callback_query

    if user_id not in ADMIN_IDS:
        await query.answer("❌ Access denied!", show_alert=True)
        return

    if data == "admin_give_sub":
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        text = ("👥 Give Subscription\n\n"
               "Send user ID and subscription type:\n"
               "Format: /givesub USER_ID premium 1\n"
               "(USER_ID premium MONTHS)\n\n"
               "Example: /givesub 123456789 premium 1")

        try:
            if query.message.caption:
                await query.edit_message_caption(
                    caption=text,
                    reply_markup=reply_markup
                )
            else:
                await query.edit_message_text(
                    text=text,
                    reply_markup=reply_markup
                )
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            await query.message.reply_text(
                text=text,
                reply_markup=reply_markup
            )

    elif data == "admin_broadcast":
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        text = ("📢 Broadcast Message\n\n"
               "Send your broadcast message with format:\n"
               "/broadcast Your message here\n\n"
               "You can use Markdown formatting.\n\n"
               "Example: /broadcast Hello everyone! 🎉")
        try:
            if query.message.caption:
                await query.edit_message_caption(
                    caption=text,
                    reply_markup=reply_markup
                )
            else:
                await query.edit_message_text(
                    text=text,
                    reply_markup=reply_markup
                )
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            await query.message.reply_text(
                text=text,
                reply_markup=reply_markup
            )

    elif data == "admin_users":
        conn = sqlite3.connect('bot_hosting.db')
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM users WHERE subscription_type = "premium"')
        premium_users = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM users WHERE subscription_type = "free"')
        free_users = cursor.fetchone()[0]

        # Get recent users (last 7 days)
        cursor.execute('SELECT COUNT(*) FROM users WHERE joined_at > datetime("now", "-7 days")')
        recent_users = cursor.fetchone()[0]

        conn.close()

        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        text = (f"👥 User Statistics\n\n"
               f"📊 Total Users: {total_users}\n"
               f"💎 Premium Users: {premium_users}\n"
               f"🆓 Free Users: {free_users}\n"
               f"🆕 New Users (7 days): {recent_users}\n\n"
               f"📈 Premium Rate: {(premium_users/total_users*100):.1f}%" if total_users > 0 else "📈 Premium Rate: 0%")
        try:
            if query.message.caption:
                await query.edit_message_caption(
                    caption=text,
                    reply_markup=reply_markup
                )
            else:
                await query.edit_message_text(
                    text=text,
                    reply_markup=reply_markup
                )
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            await query.message.reply_text(
                text=text,
                reply_markup=reply_markup
            )
