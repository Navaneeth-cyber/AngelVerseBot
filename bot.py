import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler
)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8381713017:AAESzlPZNzs1PSdkq6awxv12qCGT0VQZDMM")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8207746599"))
PORT = int(os.environ.get("PORT", 8443))
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://python-poster-bot.onrender.com")

VIDEOS_FILE = "videos.json"

# Load videos
try:
    with open(VIDEOS_FILE, "r") as f:
        VIDEOS = json.load(f)
except:
    VIDEOS = {}

def save_videos():
    with open(VIDEOS_FILE, "w") as f:
        json.dump(VIDEOS, f)

# ---------------- Conversation States ---------------- #
CHOICE, SINGLE_WAIT_VIDEO, SINGLE_NAME, MULTI_WAIT_VIDEO, MULTI_CONFIRM, MULTI_NAME_CHOICE, MULTI_NAME_INPUT = range(7)

TEMP_DATA = {}

# ---------------- Handlers ---------------- #

async def start_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized.")
        return ConversationHandler.END

    await update.message.reply_text(
        "🛠️ Admin mode activated.\nDo you want to upload Single video or Multiple videos?\nReply: single / multi"
    )
    TEMP_DATA.clear()
    TEMP_DATA["videos"] = []
    return CHOICE

# ---------- Choice Handler ----------
async def choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if text == "single":
        await update.message.reply_text("📤 Send the video for single upload:")
        return SINGLE_WAIT_VIDEO
    elif text == "multi":
        await update.message.reply_text(
            "📤 Send multiple videos one by one.\nType 'done' when finished."
        )
        return MULTI_WAIT_VIDEO
    else:
        await update.message.reply_text("⚠️ Invalid choice. Reply 'single' or 'multi'.")
        return CHOICE

# ---------- Single Video Flow ----------
async def single_video_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.video:
        await update.message.reply_text("⚠️ Please send a valid video.")
        return SINGLE_WAIT_VIDEO

    TEMP_DATA["videos"].append(update.message.video.file_id)
    await update.message.reply_text("✅ Video received. Now send the anime name:")
    return SINGLE_NAME

async def single_name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    anime_name = update.message.text.strip().replace(" ", "_").lower()
    TEMP_DATA["name"] = anime_name

    VIDEOS[anime_name] = TEMP_DATA["videos"]
    save_videos()

    link = f"https://t.me/{context.bot.username}?start={anime_name}"
    await update.message.reply_text(f"✅ Single video uploaded!\nLink: {link}")

    TEMP_DATA.clear()
    return ConversationHandler.END

# ---------- Multi Video Flow ----------
async def multi_video_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text and update.message.text.lower() == "done":
        if len(TEMP_DATA["videos"]) == 0:
            await update.message.reply_text("⚠️ No videos uploaded yet.")
            return MULTI_WAIT_VIDEO

        await update.message.reply_text(
            f"📊 Total videos uploaded: {len(TEMP_DATA['videos'])}\nConfirm upload? (yes / no)"
        )
        return MULTI_CONFIRM

    if update.message.video:
        TEMP_DATA["videos"].append(update.message.video.file_id)
        await update.message.reply_text(
            f"✅ Video {len(TEMP_DATA['videos'])} received. Send next or type 'done'."
        )
        return MULTI_WAIT_VIDEO

    await update.message.reply_text("⚠️ Send a valid video or type 'done'.")
    return MULTI_WAIT_VIDEO

async def multi_confirm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if text == "yes":
        await update.message.reply_text(
            "Do you want a single name for all videos or individual names? (all / individual)"
        )
        return MULTI_NAME_CHOICE

    elif text == "no":
        TEMP_DATA["videos"].clear()
        await update.message.reply_text("❌ Upload cancelled. Send videos again.")
        return MULTI_WAIT_VIDEO

    await update.message.reply_text("⚠️ Reply 'yes' or 'no'.")
    return MULTI_CONFIRM

async def multi_name_choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.lower()
    TEMP_DATA["names"] = []

    if choice == "all":
        TEMP_DATA["multi_name_type"] = "all"
        await update.message.reply_text("Enter the anime name for all videos:")
        return MULTI_NAME_INPUT

    elif choice == "individual":
        TEMP_DATA["multi_name_type"] = "individual"
        await update.message.reply_text(
            f"Enter names for each video, {len(TEMP_DATA['videos'])} times:"
        )
        return MULTI_NAME_INPUT

    await update.message.reply_text("⚠️ Reply 'all' or 'individual'.")
    return MULTI_NAME_CHOICE

async def multi_name_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip().replace(" ", "_").lower()
    TEMP_DATA["names"].append(name)

    if TEMP_DATA["multi_name_type"] == "all":
        VIDEOS[name] = TEMP_DATA["videos"]
        save_videos()

        link = f"https://t.me/{context.bot.username}?start={name}"
        await update.message.reply_text(f"✅ Multi-video upload done!\nLink: {link}")

        TEMP_DATA.clear()
        return ConversationHandler.END

    # Individual names
    if len(TEMP_DATA["names"]) < len(TEMP_DATA["videos"]):
        await update.message.reply_text(
            f"Enter name for video {len(TEMP_DATA['names']) + 1}:"
        )
        return MULTI_NAME_INPUT

    # Save all individual videos
    for file_id, anime_name in zip(TEMP_DATA["videos"], TEMP_DATA["names"]):
        VIDEOS[anime_name] = [file_id]

    save_videos()

    links = [
        f"https://t.me/{context.bot.username}?start={n}"
        for n in TEMP_DATA["names"]
    ]
    await update.message.reply_text("✅ Multi-video upload done!\n" + "\n".join(links))

    TEMP_DATA.clear()
    return ConversationHandler.END

# ---------- Cancel ----------
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    TEMP_DATA.clear()
    await update.message.reply_text("❌ Upload cancelled.")
    return ConversationHandler.END

# ---------------- Bot Setup ---------------- #
app = ApplicationBuilder().token(BOT_TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("admin", start_admin)],
    states={
        CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choice_handler)],
        SINGLE_WAIT_VIDEO: [MessageHandler(filters.VIDEO, single_video_handler)],
        SINGLE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, single_name_handler)],
        MULTI_WAIT_VIDEO: [
            MessageHandler(filters.VIDEO | (filters.TEXT & ~filters.COMMAND), multi_video_handler)
        ],
        MULTI_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, multi_confirm_handler)],
        MULTI_NAME_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, multi_name_choice_handler)],
        MULTI_NAME_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, multi_name_input_handler)]
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)

app.add_handler(conv_handler)

# ---------------- Webhook (CORRECTED) ---------------- #
WEBHOOK_PATH = f"webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{RENDER_URL}/{WEBHOOK_PATH}"

app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path=WEBHOOK_PATH,
    webhook_url=WEBHOOK_URL
)
