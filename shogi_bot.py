import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, InputMediaPhoto
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# ==================== НАСТРОЙКИ ====================
TOKEN = "8999275602:AAHW3Od88rtO5f_JEgxpoa-sB3FlScEneTE"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== ДАННЫЕ О ФИГУРАХ ====================
# Файлы ищутся прямо в корне репозитория (рядом с shogi_bot.py)
PIECES = {
    "ФУ": {
        "name": "Fuhyo (歩兵)",
        "ru_name": "Пешка",
        "kanji": "歩",
        "img_main": "fu.jpg",
        "img_promoted": "fu_promoted.jpg", 
        "description": (
            "♟ *Ход:* одна клетка строго вперёд.\n\n"
            "⭐ *После превращения:* доходит до зоны превращения (последние 3 горизонтали) "
            "и становится «Tokin» (と金). Начинает ходить абсолютно так же, как Золотой генерал!\n\n"
            "📜 *Правило Утифу:* запрещено ставить мат сбросом пешки с руки напрямую."
        ),
    },
    "ОУ": {
        "name": "Osho / Gyokusho (王将/玉将)",
        "ru_name": "Король",
        "kanji": "王",
        "img_main": "gyoku.jpg",
        "img_promoted": None, 
        "description": (
            "♟ *Ход:* на одну клетку в любом направлении (все 8 сторон).\n\n"
            "🎯 *Цель игры:* поймать Короля соперника и поставить ему мат."
        ),
    },
    "ХИСЯ": {
        "name": "Hisha (飛車)",
        "ru_name": "Ладья",
        "kanji": "飛",
        "img_main": "hisha.jpg",
        "img_promoted": "hisha_promoted.jpg",
        "description": (
            "♟ *Ход:* на любое количество клеток по горизонтали или вертикали.\n\n"
            "⭐ *После превращения:* становится Драконом («Ryuo»). Сохраняет ходы ладьи + добавляется ход на 1 клетку по диагоналям."
        ),
    },
    "КАКУ": {
        "name": "Kakugyo (角行)",
        "ru_name": "Слон",
        "kanji": "角",
        "img_main": "kaku.jpg",
        "img_promoted": "kaku_promoted.jpg",
        "description": (
            "♟ *Ход:* на любое количество клеток по диагонали.\n\n"
            "⭐ *После превращения:* становится Лошадью («Ryuma»). Сохраняет ходы слона + добавляется ход на 1 клетку по vertical/горизонтали."
        ),
    },
    "КИН": {
        "name": "Kinsho (金将)",
        "ru_name": "Золотой генерал",
        "kanji": "金",
        "img_main": "kin.jpg",
        "img_promoted": None,
        "description": (
            "♟ *Ход:* на 1 клетку в любую сторону, кроме как по диагонали назад (6 направлений).\n\n"
            "⚠️ Не превращается."
        ),
    },
    "ГИН": {
        "name": "Ginsho (銀将)",
        "ru_name": "Серебряный генерал",
        "kanji": "銀",
        "img_main": "gin.jpg",
        "img_promoted": "gin_promoted.jpg",
        "description": (
            "♟ *Ход:* на 1 клетку вперёд или по любым диагоналям (5 направлений).\n\n"
            "⭐ *После превращения:* ходит как Золотой генерал."
        ),
    },
    "КЭЙ": {
        "name": "Keima (桂馬)",
        "ru_name": "Конь",
        "kanji": "桂",
        "img_main": "kei.jpg",
        "img_promoted": "kei_promoted.jpg",
        "description": (
            "♟ *Ход:* буквой «Г» исключительно вперёд (на 2 клетки вперёд и 1 в сторону).\n\n"
            "⭐ *После превращения:* ходит как Золотой генерал."
        ),
    },
    "КЁ": {
        "name": "Kyosha (香車)",
        "ru_name": "Копьеносец",
        "kanji": "香",
        "img_main": "kyo.jpg",
        "img_promoted": "kyo_promoted.jpg",
        "description": (
            "♟ *Ход:* на любое количество клеток строго вперёд.\n\n"
            "⭐ *После превращения:* ходит как Золотой генерал."
        ),
    },
}

QUIZZES = [
    {
        "question": "Какая фигура в сёги ходит только вперёд на любое количество клеток?",
        "options": ["Ладья (Hisha)", "Копьеносец (Kyosha)", "Конь (Keima)", "Пешка (Fuhyo)"],
        "answer": 1,
        "explanation": "Копьеносец (Kyosha) бьет вертикаль только перед собой."
    }
]

# ==================== КЛАВИАТУРЫ ====================
def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 Изучить фигуры", callback_data="menu_pieces")],
        [InlineKeyboardButton("🧠 Пройти тест", callback_data="menu_quiz")],
        [InlineKeyboardButton("📜 Правила игры", callback_data="menu_rules")]
    ])

def pieces_menu_keyboard():
    keyboard = []
    for key, piece in PIECES.items():
        keyboard.append([InlineKeyboardButton(f"{piece['kanji']} {piece['ru_name']}", callback_data=f"piece_{key}")])
    keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")])
    return InlineKeyboardMarkup(keyboard)

def back_to_main():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад к фигурам", callback_data="menu_pieces")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")]
    ])

# ==================== КОМАНДЫ ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "🎌 *Добро пожаловать в Teacher Shogi!*\n\nВыбери раздел меню ниже:",
        parse_mode="Markdown", reply_markup=main_menu_keyboard()
    )

# ==================== ОБРАБОТЧИК КНОПОК ====================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "menu_main":
        try:
            await query.message.delete()
        except Exception:
            pass
        await query.message.chat.send_message("🎌 *Главное меню*:", parse_mode="Markdown", reply_markup=main_menu_keyboard())

    elif data == "menu_pieces":
        try:
            await query.edit_message_text("📖 *Выберите фигуру для изучения:*", parse_mode="Markdown", reply_markup=pieces_menu_keyboard())
        except Exception:
            await query.message.chat.send_message("📖 *Выберите фигуру для изучения:*", parse_mode="Markdown", reply_markup=pieces_menu_keyboard())

    elif data.startswith("piece_"):
        key = data.replace("piece_", "")
        piece = PIECES.get(key)
        
        if piece:
            caption_text = f"🔹 *{piece['name']} — {piece['ru_name']}*\n\n{piece['description']}"
            media_group = []

            # Ищем файлы прямо в корне репозитория
            if os.path.exists(piece["img_main"]):
                media_group.append(InputMediaPhoto(open(piece["img_main"], "rb"), caption=caption_text, parse_mode="Markdown"))
            
            if piece["img_promoted"] and os.path.exists(piece["img_promoted"]):
                media_group.append(InputMediaPhoto(open(piece["img_promoted"], "rb")))

            if media_group:
                try:
                    await query.message.delete()
                except Exception:
                    pass
                
                # Отправляем альбом фотографий
                await query.message.chat.send_media_group(media=media_group)
                await query.message.chat.send_message("🧭 Навигация:", reply_markup=back_to_main())
            else:
                missing_files = piece["img_main"]
                if piece["img_promoted"]:
                    missing_files += f" или {piece['img_promoted']}"
                await query.message.chat.send_message(f"⚠️ Ошибка: На GitHub не найден файл `{missing_files}`.")

    elif data == "menu_quiz":
        context.user_data["quiz_index"] = 0
        context.user_data["quiz_score"] = 0
        q = QUIZZES[0]
        keyboard = [[InlineKeyboardButton(opt, callback_data=f"quiz_ans_{i}")] for i, opt in enumerate(q["options"])]
        await query.edit_message_text(f"🧠 *Вопрос 1*\n\n{q['question']}", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("quiz_ans_"):
        await query.edit_message_text("🎉 Ответ принят! Возвращайся в меню.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="menu_main")]]))

    elif data == "menu_rules":
        await query.edit_message_text("📜 *Базовые правила:* игра идет на доске 9х9. Цель — съесть Короля. Любую съеденную фигуру соперника можно выставить за себя обратно на доску (сброс) вместо своего хода.", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="menu_main")]]))

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("🎌 Бот успешно запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
