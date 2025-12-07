import os
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8381713017:AAESzlPZNzs1PSdkq6awxv12qCGT0VQZDMM")
MAIN_CHANNEL = "@AngelVerse_main"
BACKUP_CHANNEL = "@AngelVerse_backup"
ADMIN_ID = 8207746599

PORT = int(os.environ.get("PORT", 8443))  # Render provides this

# Load videos JSON
try:
    with open("videos.json", "r") as f:
        VIDEOS = json.load(f)
except:
    VIDEOS = {}

# Save videos JSON
def save_videos():
    with open("videos.json", "w") as f:
        json.dump(VIDEOS, f)

# Command to add a video (admin only)
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized.")
        return

    if not update.message.video:
        await update.message.reply_text("⚠️ Please attach a video with this command.\nUsage: /add <anime_name>")
        return

    args = []
    if update.message.caption:
        parts = update.message.caption.split()
        if parts[0].lower() == "/add":
            args = parts[1:]
    if not args:
        args = context.args

    if not args:
        await update.message.reply_text("⚠️ Please provide anime name. Usage: /add <anime_name>")
        return

    anime_name = "_".join(args).replace(" ", "_").lower()
    file_id = update.message.video.file_id

    VIDEOS[anime_name] = file_id
    save_videos()

    link = f"https://t.me/AngelVerse_bot?start={anime_name}"
    await update.message.reply_text(f"✅ Video saved!\nPost this link in your channel:\n{link}")

# Start command (for users clicking link)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args

    if not args:
        await update.message.reply_text("⚠️ Please click the link from the channel to get the anime.")
        return

    anime_id = args[0]

    # Check channel join
    main = await context.bot.get_chat_member(MAIN_CHANNEL, user_id)
    main_joined = main.status in ["member", "administrator", "creator"]

    backup = await context.bot.get_chat_member(BACKUP_CHANNEL, user_id)
    backup_joined = backup.status in ["member", "administrator", "creator"]

    if not (main_joined and backup_joined):
        await update.message.reply_text("⚠️ You must join BOTH channels to get the anime!")
        return

    file_id = VIDEOS.get(anime_id)
    if file_id:
        await update.message.reply_video(video=file_id)
    else:
        await update.message.reply_text("❌ Anime not found!")

# Build the app
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("add", add))
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.VIDEO, add))

# Webhook URL
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://angelversebot.onrender.com")
WEBHOOK_URL = f"{RENDER_URL}/{BOT_TOKEN}"

# Run webhook
app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path=BOT_TOKEN,
    webhook_url=WEBHOOK_URL
)

