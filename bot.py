import logging
from telegram import Update, ReactionTypeEmoji
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Configuration
BOT_TOKEN = "7880676293:AAEW4qqSV11lcI8MnjtYXRRgQUuqYdgTyOk"
ALLOWED_USER_IDS = []  # Add permitted user IDs for commands (empty = all users)
REACTION_RULES = {
    "🔥": ["awesome", "fire", "lit"],
    "❤️": ["love", "heart", "like"],
    "👍": ["good", "yes", "agree"],
    "👎": ["bad", "no", "disagree"],
    "😂": ["lol", "haha", "funny"]
}

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message"""
    await update.message.reply_text("🤖 Reaction Bot Active! I'll react to messages with keywords.")

async def react_to_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Automatically react to messages based on keywords"""
    message = update.message
    if not message or not message.text:
        return
    
    text = message.text.lower()
    reactions_to_add = []
    
    # Check for matching keywords
    for emoji, keywords in REACTION_RULES.items():
        if any(keyword in text for keyword in keywords):
            reactions_to_add.append(ReactionTypeEmoji(emoji))
    
    # Add reactions if matches found
    if reactions_to_add:
        try:
            await message.reply_reaction(reactions_to_add)
        except Exception as e:
            logging.error(f"Reaction failed: {e}")

async def manual_react(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """React to a message when replied to with /react command"""
    user = update.effective_user
    if ALLOWED_USER_IDS and user.id not in ALLOWED_USER_IDS:
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Please reply to a message to react!")
        return
    
    try:
        emoji = context.args[0] if context.args else "👍"
        await update.message.reply_to_message.reply_reaction([ReactionTypeEmoji(emoji)])
        await update.message.delete()
    except Exception as e:
        logging.error(f"Manual reaction failed: {e}")
        await update.message.reply_text("❌ Invalid emoji or reaction failed")

def main():
    # Create bot application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("react", manual_react))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, react_to_message))
    
    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()