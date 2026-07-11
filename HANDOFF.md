# HANDOFF — Bronislav Bot (@Bronislavbro_bot)

## Что это
Telegram-бот, персона философа/синолога Бронислава Виноградского.
GPT-4o-mini + Whisper + TTS, с памятью последних 10 обменов на пользователя.

## Стек (main.py)
- python-telegram-bot: InlineKeyboardButton/InlineKeyboardMarkup
- OpenAI client: images.generate (gpt-image-1, размер 1024x1024) для "Нарисуй"
- OpenAI TTS: audio.speech.create (model="tts-1", voice="echo")
- Ответы голосом: reply_voice из локального reply.mp3

## Inline-клавиатура (main.py ~строка 45-49)
- "✨ Мудрость" → callback_data="wisdom"
- "🖌 Нарисуй" → callback_data="draw" (генерация через gpt-image-1)
- "🔄 Забыть всё" → callback_data="clear" (сброс истории диалога)

## Инфраструктура
- GitHub repo: paninsergey1965-lgtm/bronislav-bot
- Railway project: "remarkable-quietude" (по памяти прошлых сессий,
  не проверено в этой сессии — уточнить при следующем заходе)
- Аватар бота: картина "Снисходительность"

## Системный промпт
Стилизован под манеру речи Виноградского: короткие резкие фразы,
парадоксальные формулировки, отсутствие прямых советов,
самоирония, бытовые метафоры из разных сфер (не повторяющиеся).

## Не сделано / открыто
- HANDOFF.md создан только сейчас (11.07.2026), задним числом
- Railway project ID/URL не подтверждён в этой сессии
