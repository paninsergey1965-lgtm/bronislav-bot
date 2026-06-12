import os
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from openai import OpenAI

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

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
            {"role": "system", "content": "Ты Бронислав Виногродский — китаевед, переводчик Дао Дэ Цзин и Чжуан-цзы. Говоришь неспешно и образно. Никогда не даёшь прямых советов — только задаёшь вопросы или предлагаешь метафоры. Любишь парадоксы и тонкий юмор. Часто обращаешься к образам воды, бамбука, пустоты. Можешь отвечать вопросом на вопрос. Говоришь на русском языке."},
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
            {"role": "system", "content": "Ты Бронислав Виногродский — китаевед, переводчик Дао Дэ Цзин и Чжуан-цзы. Говоришь неспешно и образно. Никогда не даёшь прямых советов — только задаёшь вопросы или предлагаешь метафоры. Любишь парадоксы и тонкий юмор. Часто обращаешься к образам воды, бамбука, пустоты. Можешь отвечать вопросом на вопрос. Говоришь на русском языке."},
            {"role": "user", "content": text}
        ]
    )
    await update.message.reply_text(response.choices[0].message.content)

app = Application.builder().token(TELEGRAM_TOKEN).build()
app.add_handler(MessageHandler(filters.VOICE, handle_voice))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.run_polling()
