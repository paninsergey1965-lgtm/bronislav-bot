import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CallbackQueryHandler, CommandHandler
from openai import OpenAI
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_KEY)

SYSTEM_PROMPT = "Ты Бронислав Виногродский — китаевед, переводчик Дао Дэ Цзин и Чжуан-цзы. Говоришь без пафоса, иногда грубовато: хрен там, ну и чё, плевать я хотел. Короткие рубленые фразы после длинных. Любишь парадоксальные формулы: жизнь — это не повод для беспокойства, умный с блеском выходит из ситуации в которую мудрый никогда не попадёт. Проблемы называешь болезнью а не чертой. Используешь бытовые образы — кот вокруг коробки, рыбак который не бросает сеть в каждую лужу. Не даёшь советов — предлагаешь посмотреть самому. Говоришь на русском. Отвечаешь коротко — 3-5 предложений."

conversation_history = {}
MAX_HISTORY = 10

def get_history(user_id):
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    return conversation_history[user_id]

def add_to_history(user_id, role, content):
    history = get_history(user_id)
    history.append({"role": role, "content": content})
    if len(history) > MAX_HISTORY * 2:
        conversation_history[user_id] = history[-MAX_HISTORY * 2:]

def get_keyboard():
    keyboard = [
        [InlineKeyboardButton("Мудрость", callback_data="wisdom"),
         InlineKeyboardButton("Нарисуй", callback_data="draw"),
         InlineKeyboardButton("Забыть всё", callback_data="clear")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conversation_history[user_id] = []
    await update.message.reply_text("Доброе утро добрым людям.", reply_markup=get_keyboard())

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if query.data == "forecast":
        history = get_history(user_id)
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history + [{"role": "user", "content": "Ты Бронислав Виногродский — китаевед, переводчик Дао Дэ Цзин и Чжуан-цзы. Говоришь без пафоса, иногда грубовато: хрен там, ну и чё, плевать я хотел. Короткие рубленые фразы после длинных. Любишь парадоксальные формулы: жизнь — это не повод для беспокойства, умный с блеском выходит из ситуации в которую мудрый никогда не попадёт, судьба готовится на медленном огне, созревший плод не кричит о своей спелости. Проблемы называешь болезнью а не чертой. Используешь разные бытовые образы — рыбак, садовник, повар, фасоль в кастрюле, старая телега, намоченный хвост. Каждый раз выбираешь новый образ, не повторяешься. Не даёшь советов — предлагаешь посмотреть самому. Говоришь на русском. Отвечаешь коротко — 3-5 предложений."}]
        response = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
        text = response.choices[0].message.content
        await query.message.reply_text(text, reply_markup=get_keyboard())
    elif query.data == "wisdom":
        messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": "Скажи одну короткую мудрость — свою любимую формулу. Одно-два предложения."}]
        response = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
        text = response.choices[0].message.content
        await query.message.reply_text(text, reply_markup=get_keyboard())
    elif query.data == "draw":
        await query.message.reply_text("Рисую...")
        history = get_history(user_id)
        context_text = " ".join([m["content"] for m in history[-4:]]) if history else "daoist philosophy, change, the way"
        prompt_msg = [{"role": "user", "content": "Based on this conversation, write a short image description for Chinese ink wash painting style. English only, 1-2 sentences. Context: " + context_text}]
        prompt_response = client.chat.completions.create(model="gpt-4o-mini", messages=prompt_msg)
        image_prompt = "Chinese ink wash painting, minimalist, " + prompt_response.choices[0].message.content
        image_response = client.images.generate(model="dall-e-3", prompt=image_prompt, size="1024x1024", n=1)
        await query.message.reply_photo(photo=image_response.data[0].url, reply_markup=get_keyboard())
    elif query.data == "clear":
        conversation_history[user_id] = []
        await query.message.reply_text("Забыл всё. Начнём заново.", reply_markup=get_keyboard())

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)
    await file.download_to_drive("voice.ogg")
    with open("voice.ogg", "rb") as f:
        transcript = client.audio.transcriptions.create(model="whisper-1", file=f)
    text = transcript.text
    add_to_history(user_id, "user", text)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + get_history(user_id)
    response = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
    reply_text = response.choices[0].message.content
    add_to_history(user_id, "assistant", reply_text)
    tts = client.audio.speech.create(model="tts-1", voice="echo", input=reply_text)
    tts.stream_to_file("reply.mp3")
    await update.message.reply_voice(voice=open("reply.mp3", "rb"), reply_markup=get_keyboard())

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    add_to_history(user_id, "user", text)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + get_history(user_id)
    response = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
    reply_text = response.choices[0].message.content
    add_to_history(user_id, "assistant", reply_text)
    await update.message.reply_text(reply_text, reply_markup=get_keyboard())

app = Application.builder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle_callback))
app.add_handler(MessageHandler(filters.VOICE, handle_voice))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.run_polling()
