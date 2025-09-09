import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes,
    MessageHandler, filters
)
import config
from helpers import (
    generate_paytm_qr, store_key, get_keys, delete_key, get_invoice,
    owner_notify, get_mod_file, store_mod_file, is_owner,
    LANG, set_lang
)

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("🛒 Buy Mod/Loader", callback_data="buy_mod")],
        [InlineKeyboardButton("📢 Channel ", callback_data="channel")],
        [InlineKeyboardButton("👑 Owner", callback_data="owner")],
    ]
    text = "Welcome! 👋\n\nWhat can this bot do?\n\n1️⃣ Buy Mods/Loaders\n2️⃣ Join Channel\n3️⃣ Contact Owner\n"
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def buy_mod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🧱 WallHack", callback_data="wallhack")],
        [InlineKeyboardButton("🎯 ESP/AimBot ", callback_data="esp")],
        [InlineKeyboardButton("🔙 Back ", callback_data="start")],
    ]
    await update.callback_query.edit_message_text("Select your product:\n\n", reply_markup=InlineKeyboardMarkup(keyboard))

async def wallhack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🗓️ Week (₹150)=", callback_data="wallhack_week")],
        [InlineKeyboardButton("📅 Month (₹350) ", callback_data="wallhack_month")],
        [InlineKeyboardButton("🛡️ Season (₹600)", callback_data="wallhack_season")],
        [InlineKeyboardButton("🔙 Back", callback_data="buy_mod")],
    ]
    await update.callback_query.edit_message_text("WallHack Options:\n\n", reply_markup=InlineKeyboardMarkup(keyboard))

async def esp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📆 Day (₹150) ", callback_data="esp_day")],
        [InlineKeyboardButton("🕒 3 Days (₹300)", callback_data="esp_3day")],
        [InlineKeyboardButton("🗓️ Week (₹500)", callback_data="esp_week")],
        [InlineKeyboardButton("📅 Month (₹800) ", callback_data="esp_month")],
        [InlineKeyboardButton("🛡️ Season (₹1200)", callback_data="esp_season")],
        [InlineKeyboardButton("🔙 Backं", callback_data="buy_mod")],
    ]
    await update.callback_query.edit_message_text("ESP/AimBot Options:\n\n", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    product_map = {
        "wallhack_week": ("WallHack", "Week", 150),
        "wallhack_month": ("WallHack", "Month", 350),
        "wallhack_season": ("WallHack", "Season", 600),
        "esp_day": ("ESP/AimBot", "Day", 150),
        "esp_3day": ("ESP/AimBot", "3 Day", 300),
        "esp_week": ("ESP/AimBot", "Week", 500),
        "esp_month": ("ESP/AimBot", "Month", 800),
        "esp_season": ("ESP/AimBot", "Season", 1200),
    }
    prod, duration, price = product_map[query.data]
    qr_img, paytm_id = generate_paytm_qr(price)
    context.user_data["pending_purchase"] = {
        "product": prod, "duration": duration, "price": price, "paytm_id": paytm_id,
    }
    text = (f"Pay ₹{price} for {prod} ({duration})\n\n ₹{price} {prod} ({duration})\n\n"
        "Scan this QR code with Paytm to pay.\n\n")
    await query.edit_message_text(text)
    await query.message.reply_photo(qr_img, caption="Paytm QR ")
    await owner_notify(context, update.effective_user, prod, duration, price)

async def payment_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    purchase = context.user_data.get("pending_purchase")
    if not purchase:
        await update.message.reply_text("No pending purchase found.")
        return
    mod_file, key, mod_caption = get_mod_file(purchase["product"], purchase["duration"])
    if not mod_file or not key:
        await update.message.reply_text("Currently, this product is out of stock.")
        return
    delete_key(purchase["product"], purchase["duration"], key)
    invoice = get_invoice(user, purchase, key)
    await update.message.reply_document(mod_file, caption=mod_caption)
    await update.message.reply_text(invoice, parse_mode=ParseMode.MARKDOWN)

async def keys(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("Not authorized.")
        return
    all_keys = get_keys()
    text = "Available Keys:\n\n\n"
    for prod, durations in all_keys.items():
        for duration, keys in durations.items():
            text += f"\n*{prod} ({duration}):*\n" + "\n".join(keys)
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def upload_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("Not authorized.")
        return
    await update.message.reply_text(
        "Send product name (WallHack/ESP), duration and key separated by commas:\n\nExample: WallHack,Week,ABCD-1234"
    )
    context.user_data["awaiting_key_upload"] = True

async def receive_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_key_upload"):
        return
    parts = update.message.text.split(",")
    if len(parts) != 3:
        await update.message.reply_text("Invalid format. Try again.\n")
        return
    prod, duration, key = [p.strip() for p in parts]
    store_key(prod, duration, key)
    await update.message.reply_text(f"Key uploaded for {prod} ({duration}).")
    context.user_data["awaiting_key_upload"] = False

async def upload_mod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("Not authorized.")
        return
    await update.message.reply_text(
        "Upload the mod file as a document (zip/apk), and in the caption write: product,duration\n\nExample: WallHack,Week"
    )
    context.user_data["awaiting_mod_upload"] = True

async def receive_mod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_mod_upload"):
        return
    if not update.message.document or not update.message.caption:
        await update.message.reply_text("Please upload a document (zip/apk) with proper caption.")
        return
    parts = update.message.caption.split(",")
    if len(parts) != 2:
        await update.message.reply_text("Invalid caption format. Try again.\nगलत प्रारूप। फिर कोशिश करें।")
        return
    prod, duration = [p.strip() for p in parts]
    file_id = update.message.document.file_id
    file_name = update.message.document.file_name or "modfile"
    store_mod_file(prod, duration, file_id, file_name)
    await update.message.reply_text(f"Mod uploaded for {prod} ({duration}).\n")
    context.user_data["awaiting_mod_upload"] = False

async def channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text(
        f"Join our channel for updates:\n\n👉 [Channel Link]({config.CHANNEL_LINK})",
        parse_mode=ParseMode.MARKDOWN,
    )

async def owner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text(
        f"Contact owner:\n👑 [Owner]({config.OWNER_LINK})",
        parse_mode=ParseMode.MARKDOWN,
    )

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🇮🇳 ", callback_data="lang_hi"),
         InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")]
    ]
    await update.message.reply_text(
        "Choose your language:", reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def change_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = "hi" if update.callback_query.data == "lang_hi" else "en"
    set_lang(update.effective_user.id, lang)
    await update.callback_query.edit_message_text(
        "Language updated!"
    )

def main():
    application = Application.builder().token(config.BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("keys", keys))
    application.add_handler(CommandHandler("key", upload_key))
    application.add_handler(CommandHandler("language", set_language))
    application.add_handler(CommandHandler("mod", upload_mod))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_key))
    application.add_handler(MessageHandler(filters.Document.ALL, receive_mod))
    application.add_handler(CallbackQueryHandler(buy_mod, pattern="buy_mod"))
    application.add_handler(CallbackQueryHandler(wallhack, pattern="wallhack"))
    application.add_handler(CallbackQueryHandler(esp, pattern="esp"))
    application.add_handler(CallbackQueryHandler(handle_payment, pattern="wallhack_week|wallhack_month|wallhack_season|esp_day|esp_3day|esp_week|esp_month|esp_season"))
    application.add_handler(CallbackQueryHandler(channel, pattern="channel"))
    application.add_handler(CallbackQueryHandler(owner, pattern="owner"))
    application.add_handler(CallbackQueryHandler(change_language, pattern="lang_hi|lang_en"))
    application.add_handler(MessageHandler(filters.Regex("I have paid"), payment_done))
    application.run_polling()

if __name__ == "__main__":
    main()