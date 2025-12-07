import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler
)

# -------------------------------------- #
#               CONFIG                   #
# -------------------------------------- #

BOT_TOKEN = "8381713017:AAESzlPZNzs1PSdkq6awxv12qCGT0VQZDMM"
ADMIN_ID = 8207746599
VIDEOS_FILE = "videos.json"

# -------------------------------------- #
#        LOAD / SAVE VIDEO DATA          #
# -------------------------------------- #

try:
    with open(VIDEOS_FILE, "r") as f:
        VIDEOS = json.load(f)
except:
    VIDEOS = {}

def save_videos():
    with open(VIDEOS_FILE, "w") as f:
        json.dump(VIDEOS, f)

# -------------------------------------- #
#         CONVERSATION STATES            #
# -------------------------------------- #

(
    CHOICE,
    SINGLE_WAIT_VIDEO,
    SINGLE_NAME,
    MULTI_WAIT_VIDEO,
    MULTI_CONFIRM,
    MULTI_NAME_CHOICE,
    MULTI_NAME_INPUT
) = range(7)

TEMP_DATA = {}

# -------------------------------------- #
#               HANDLERS                 #
# -------------------------------------- #

async def start_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized.")
        return ConversationHandler.END

    await update.message.reply_text(
        "🛠️ Admin mode activated.\n"
        "Upload Type?\n👉 single / multi"
    )

    TEMP_DATA.clear()
    TEMP_DATA["videos"] = []
    return CHOICE


# ---------- Choice ---------- #
async def choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    if text == "single":
        await update.message.reply_text("📤 Send **one** video:")
        return SINGLE_WAIT_VIDEO

    elif text == "multi":
        await update.message.reply_text(
            "📤 Send videos **one by one**.\nType 'done' when finished."
        )
        return MULTI_WAIT_VIDEO

    else:
        await update.message.reply_text("⚠️ Reply only: single / multi")
        return CHOICE


# ---------- Single Video ---------- #
async def single_video_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.video:
        await update.message.reply_text("⚠️ Please send a valid video.")
        return SINGLE_WAIT_VIDEO

    TEMP_DATA["videos"].append(update.message.video.file_id)

    await update.message.reply_text("✔️ Video received.\nEnter anime name:")
    return SINGLE_NAME


async def single_name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    anime_name = update.message.text.strip().replace(" ", "_").lower()
    TEMP_DATA["name"] = anime_name

    VIDEOS[anime_name] = TEMP_DATA["videos"]
    save_videos()

    link = f"https://t.me/{context.bot.username}?start={anime_name}"
    await update.message.reply_text(f"✅ Uploaded!\n🔗 Link: {link}")

    TEMP_DATA.clear()
    return ConversationHandler.END


# ---------- Multi Video Upload ---------- #
async def multi_video_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Finished
    if update.message.text and update.message.text.lower() == "done":
        if len(TEMP_DATA["videos"]) == 0:
            await update.message.reply_text("⚠️ No videos uploaded yet!")
            return MULTI_WAIT_VIDEO

        await update.message.reply_text(
            f"📊 Total videos: {len(TEMP_DATA['videos'])}\n"
            "Confirm upload? yes / no"
        )
        return MULTI_CONFIRM

    # Add video
    if update.message.video:
        TEMP_DATA["videos"].append(update.message.video.file_id)
        await update.message.reply_text(
            f"✔️ Video {len(TEMP_DATA['videos'])} received.\nSend next or type 'done'."
        )
        return MULTI_WAIT_VIDEO

    await update.message.reply_text("⚠️ Send a video or 'done'.")
    return MULTI_WAIT_VIDEO


async def multi_confirm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    if text == "yes":
        await update.message.reply_text("Name type? all / individual")
        return MULTI_NAME_CHOICE

    elif text == "no":
        TEMP_DATA["videos"].clear()
        await update.message.reply_text("❌ Cancelled. Send videos again.")
        return MULTI_WAIT_VIDEO

    else:
        await update.message.reply_text("⚠️ Reply: yes / no")
        return MULTI_CONFIRM


async def multi_name_choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.lower()

    TEMP_DATA["names"] = []

    if choice == "all":
        TEMP_DATA["multi_name_type"] = "all"
        await update.message.reply_text("Enter ONE anime name for all videos:")
        return MULTI_NAME_INPUT

    elif choice == "individual":
        TEMP_DATA["multi_name_type"] = "individual"
        await update.message.reply_text(
            f"Enter names for {len(TEMP_DATA['videos'])} videos:"
        )
        return MULTI_NAME_INPUT

    await update.message.reply_text("⚠️ Reply: all / individual")
    return MULTI_NAME_CHOICE


async def multi_name_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip().replace(" ", "_").lower()
    TEMP_DATA["names"].append(name)

    # ONE NAME for all videos
    if TEMP_DATA["multi_name_type"] == "all":
        VIDEOS[name] = TEMP_DATA["videos"]
        save_videos()

        link = f"https://t.me/{context.bot.username}?start={name}"
        await update.message.reply_text(f"✅ Uploaded!\n🔗 Link: {link}")

        TEMP_DATA.clear()
        return ConversationHandler.END

    # INDIVIDUAL NAMES
    if len(TEMP_DATA["names"]) < len(TEMP_DATA["videos"]):
        await update.message.reply_text(
            f"Enter name for video {len(TEMP_DATA['names']) + 1}:"
        )
        return MULTI_NAME_INPUT

    # Save all separate
    for file_id, anime_name in zip(TEMP_DATA["videos"], TEMP_DATA["names"]):
        VIDEOS[anime_name] = [file_id]

    save_videos()

    # Generate links
    links = [
        f"https://t.me/{context.bot.username}?start={name}"
        for name in TEMP_DATA["names"]
    ]

    await update.message.reply_text("✅ Multi upload complete:\n" + "\n".join(links))

    TEMP_DATA.clear()
    return ConversationHandler.END


# ---------- Cancel ---------- #
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    TEMP_DATA.clear()
    await update.message.reply_text("❌ Cancelled.")
    return ConversationHandler.END


# -------------------------------------- #
#     FINAL: RUN THE BOT USING POLLING   #
# -------------------------------------- #

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(conv_handler)

async def main():
    print("🚀 Bot running with POLLING... (no webhook needed)")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.idle()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
