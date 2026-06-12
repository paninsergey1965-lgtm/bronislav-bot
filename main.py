import os
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from openai import OpenAI

TELEGRAM_TOKEN = "8757978497:AAF7YP2ttSDNrMwY_3REV-_7tuXUS4k0TUA"
OPENAI_KEY = "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"

client = OpenAI(api_key=OPENAI_KEY)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)
    await file.download_to_drive("voice.ogg")
    with open("voice.ogg", "rb") as f:
        transcript = client.audio.transcriptions.create(model="whisper-1", file=f)
    text = transcript.text
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Ты остроумный собеседник который подкалывает и подшучивает над пользователем с юмором. Отвечай коротко и смешно на русском языке."},
            {"role": "user", "content": text}
        ]
    )
    reply_text = response.choices[0].message.content
    tts = client.audio.speech.create(model="tts-1", voice="echo", input=reply_text)
    tts.stream_to_file("reply.mp3")
    await update.message.reply_voice(voice=open("reply.mp3", "rb"))

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Ты остроумный собеседник который подкалывает и подшучивает над пользователем с юмором. Отвечай коротко и смешно на русском языке."},
            {"role": "user", "content": text}
        ]
    )
    await update.message.reply_text(response.choices[0].message.content)

app = Application.builder().token(TELEGRAM_TOKEN).build()
app.add_handler(MessageHandler(filters.VOICE, handle_voice))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.run_polling()
