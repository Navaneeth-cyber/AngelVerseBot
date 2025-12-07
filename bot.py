import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = "8381713017:AAESzlPZNzs1PSdkq6awxv12qCGT0VQZDMM"
MAIN_CHANNEL = "@AngelVerse_main"
BACKUP_CHANNEL = "@AngelVerse_backup"
ADMIN_ID = 8207746599  # <-- Your Telegram user ID

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

    # Check if video is attached
    if not update.message.video:
        await update.message.reply_text("⚠️ Please attach a video with this command.\nUsage: /add <anime_name>")
        return

    # Get anime name from caption or command args
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

    anime_name = "_".join(args).lower()  # e.g. Naruto Ep1 → naruto_ep1

    # Get file_id
    file_id = update.message.video.file_id

    # Save to JSON
    VIDEOS[anime_name] = file_id
    save_videos()

    # Send back the link
    link = f"https://t.me/AngelVerse_bot?start={anime_name}"
    await update.message.reply_text(f"✅ Video saved!\nPost this link in your channel:\n{link}")

# Start command (for users clicking link)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args

    if not args:
        await update.message.reply_text("⚠️ Please click the link from the channel to get the anime.")
        return

    anime_id = args[0]  # e.g. naruto_ep1

    # Check channel join
    main = await context.bot.get_chat_member(MAIN_CHANNEL, user_id)
    main_joined = main.status in ["member", "administrator", "creator"]

    backup = await context.bot.get_chat_member(BACKUP_CHANNEL, user_id)
    backup_joined = backup.status in ["member", "administrator", "creator"]

    if not (main_joined and backup_joined):
        await update.message.reply_text("⚠️ You must join BOTH channels to get the anime!")
        return

    # Send the requested video
    file_id = VIDEOS.get(anime_id)
    if file_id:
        await update.message.reply_video(video=file_id)
    else:
        await update.message.reply_text("❌ Anime not found!")

# Handlers
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("add", add))
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.VIDEO, add))

# Run the bot
app.run_polling()
