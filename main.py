import io
import os
import config
import discord
import asyncio
import logging
import tempfile
from typing import Union
from discord.ext import commands
from moviepy.editor import VideoFileClip
from telegram import Update, Document, Animation, PhotoSize
from telegram.ext import (
    filters,
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    Defaults,
)

logging.getLogger("httpx").setLevel(level=logging.WARNING)
logging.basicConfig(level=logging.INFO)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

async def get_file(file_object: Union[Document, Animation, PhotoSize], file_name=None):
    bytes_object = io.BytesIO()
    file = await file_object.get_file()
    await file.download_to_memory(out=bytes_object)
    bytes_object.seek(0)
    return discord.File(bytes_object, filename=file_name or file_object.file_name)


async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    channel = bot.get_channel(config.CHANNEL_ID)
    text = f"**{update.effective_user.username or update.effective_user.full_name}**: "
    text += update.effective_message.text or update.effective_message.caption or ""

    if any(word.startswith("http") and "x.com" not in word for word in (text).split()):
        logging.info("Link detected, message will not be forwarded")
        return

    if update.message.text:
        await channel.send(text)

    elif animation := update.message.animation:
        with tempfile.TemporaryDirectory() as temp_folder:
            animation_file = await animation.get_file()

            mp4_file = os.path.join(temp_folder, animation.file_id)
            gif_file = mp4_file + ".gif"

            await animation_file.download_to_drive(custom_path=mp4_file)
            videoClip = VideoFileClip(mp4_file)
            videoClip.write_gif(gif_file, fps=25, program="ffmpeg")
            discord_file = discord.File(gif_file)
            await channel.send(file=discord_file, content=text)

    elif document := update.message.document:
        file = await get_file(document)
        await channel.send(file=file, content=text)

    elif photo := update.message.photo:
        file = await get_file(photo[-1], "image.png")
        await channel.send(file=file, content=text)


@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")


application = (
    ApplicationBuilder().token(config.BOT_TOKEN).defaults(Defaults(block=False)).build()
)
application.add_handler(
    MessageHandler(filters=filters.ALL & ~filters.UpdateType.EDITED, callback=handler)
)


async def main():
    await application.initialize()
    await application.start()
    await application.updater.start_webhook(webhook_url="https://ee5c4680-a568-439f-a846-4aec801b5644-00-33lvsxyuimax8.pike.replit.dev", listen='0.0.0.0', port=5001)
    await bot.start(config.DISCORD_TOKEN)
    await application.updater.stop()
    await application.stop()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
