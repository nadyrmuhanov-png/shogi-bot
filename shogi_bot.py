
import logging
import os
import io
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
PIECES = {
    "ОУ": {
        "name": "Osho / Gyokusho (王将/玉将)",
        "ru_name": "Король",
        "emoji": "♔",
        "img_main": "gyoku.jpg",
        "img_promoted": None,
        "description": (
            "Самая главная фигура в сёги — Король.\n\n"
            "♟ Ход: на одну клетку в любом направлении (8 вариантов).\n"
            "🎯 Цель игры: поставить мат королю противника."
        ),
    },
    "ХИСЯ": {
        "name": "Hisha (飛車)",
        "ru_name": "Ладья",
        "emoji": "♜",
        "img_main": "hisha.jpg",
        "img_promoted": "hisha_promoted.jpg",
        "description": (
            "Hisha (飛車) — Ладья, одна из сильнейших фигур.\n\n"
            "♟ Ход: любое количество клеток по горизонтали или вертикали.\n"
            "⭐ После превращения: становится «Ryuo» (龍王) — Король-дракон."
        ),
    },
    "КАКУ": {
        "name": "Kakugyo (角行)",
        "ru_name": "Слон",
        "emoji": "♗",
        "img_main": "kaku.jpg",
        "img_promoted": "kaku_promoted.jpg",
        "description": (
            "Kakugyo (角行) — Слон.\n\n"
            "♟ Ход: любое количество клеток по диагонали.\n"
            "⭐ После превращения: становится «Ryuma» (龍馬) — Конь-дракон."
        ),
    },
    "КИН": {
        "name": "Kinsho (金将)",
        "ru_name": "Золотой генерал",
        "emoji": "🥇",
        "img_main": "kin.jpg",
        "img_promoted": None,
        "description": (
            "Kinsho (金将) — Золотой генерал.\n\n"
            "♟ Ход: одна клетка — вперёд, назад, влево, вправо, или вперёд по диагонали (6 направлений).\n"
            "⚠️ Не превращается."
        ),
    },
    "ГИН": {
        "name": "Ginsho (銀将)",
        "ru_name": "Серебряный генерал",
        "emoji": "🥈",
        "img_main": "gin.jpg",
        "img_promoted": "gin_promoted.jpg",
        "description": (
            "Ginsho (銀将) — Серебряный генерал.\n\n"
            "♟ Ход: одна клетка — вперёд, или по диагонали в любую сторону (5 направлений).\n"
            "⭐ После превращения: ходит как Золотой генерал."
        ),
    },
    "КЭЙ": {
        "name": "Keima (桂馬)",
        "ru_name": "Конь",
        "emoji": "♞",
        "img_main": "kei.jpg",
        "img_promoted": "kei_promoted.jpg",
        "description": (
            "Keima (桂馬) — Конь.\n\n"
            "♟ Ход: прыжок — на две клетки вперёд и одну в сторону (только вперёд!).\n"
            "⭐ После превращения: ходит как Золотой генерал."
        ),
    },
    "КЁ": {
        "name": "Kyosha (香車)",
        "ru_name": "Копьеносец",
        "emoji": "🏹",
        "img_main": "kyo.jpg",
        "img_promoted": "kyo_promoted.jpg",
        "description": (
            "Kyosha (香車) — Копьеносец.\n\n"
            "♟ Ход: любое количество клеток только вперёд.\n"
            "⭐ После превращения: ходит как Золотой генерал."
        ),
    },
    "ФУ": {
        "name": "Fuhyo (歩兵)",
        "ru_name": "Пешка",
        "emoji": "♟",
        "img_main": "fu.jpg",
        "img_promoted": "fu_promoted.jpg",
        "description": (
            "Fuhyo (歩兵) — Пешка.\n\n"
            "♟ Ход: одна клетка вперёд.\n"
            "⭐ После превращения: становится «Tokin» (と金) — ходит как Золотой генерал."
        ),
    },
}

# ==================== ТЕСТЫ ====================
QUIZZES = [
    {
        "question": "Какая фигура в сёги ходит только вперёд на любое количество клеток?",
        "options": ["Ладья (Hisha)", "Копьеносец (Kyosha)", "Конь (Keima)", "Пешка (Fuhyo)"],
        "answer": 1,
        "explanation": "Копьеносец (Kyosha) ходит только вперёд на любое количество клеток."
    },
    {
        "question": "Как называется превращённая Ладья (Hisha)?",
        "options": ["Ryuma (龍馬)", "Tokin (と金)", "Ryuo (龍王)", "Narikin"],
        "answer": 2,
        "explanation": "Превращённая Ладья называется Ryuo (龍王) — Король-дракон."
    },
]

# ==================== ЗАДАЧИ (С ИСПОЛЬЗОВАНИЕМ ФОТО) ====================
PUZZLES = [
    {
        "title": "Задача 1: Запрещённый мат",
        "description": (
            "Король чёрных стоит на 1a. Пешка белых стоит на 1b.\n\n"
            "❓ Что произойдёт если пешка СБРОСОМ из руки встанет на 1b (вместо короля)?"
        ),
        "image": "task1.png",
        "options": [
            "Пешка съест Короля — победа!",
            "Это запрещённый ход (утифу) — мат пешкой со сброса запрещён",
            "Пешка превратится в Tokin",
            "Это обычный мат"
        ],
        "answer": 1,
        "explanation": "В сёги запрещено ставить мат королю сбросом пешки из руки (правило Утифудзумэ)."
    },
    {
        "title": "Задача 2: Защита сбросом",
        "description": (
            "Вражеская Ладья на 1b ставит шах вашему Королю на 3b.\n"
            "У вас в руке есть захваченный Золотой генерал.\n\n"
            "❓ Как лучше всего защититься?"
        ),
        "image": "task2.png",
        "options": [
            "Убежать Королём в сторону",
            "Сбросить Золотого генерала на поле 2b",
            "Сдаться",
            "Ничего не делать"
        ],
        "answer": 1,
        "explanation": "Сброс Золотого генерала на 2b блокирует линию атаки ладьи и защищает короля."
    },
    {
        "title": "Задача 3: Превращение пешки",
        "description": (
            "Пешка белых дошла до самого края доски (1-й ряд) — позиция 1a.\n\n"
            "❓ Что должно произойти?"
        ),
        "image": "task3.png",
        "options": [
            "Пешка остаётся пешкой",
            "Пешка обязана превратиться в Tokin",
            "Пешка убирается с доски",
            "Ничего не происходит"
        ],
        "answer": 1,
        "explanation": "Фигура обязана превратиться, если у неё больше нет возможности сделать ход (для пешки это 1-й ряд)."
    },
]

# ==================== КЛАВИАТУРЫ ====================
def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 Изучить фигуры", callback_data="menu_pieces")],
        [InlineKeyboardButton("🧠 Пройти тест", callback_data="menu_quiz")],
        [InlineKeyboardButton("♟ Задачи на ход", callback_data="menu_puzzles")],
        [InlineKeyboardButton("📜 Правила игры", callback_data="menu_rules")]
    ])

def pieces_menu_keyboard():
    keyboard = []
    for key, piece in PIECES.items():
        btn_text = f"{piece['emoji']} {piece['ru_name']}"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"piece_{key}")])
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
        "🎌 *Добро пожаловать в Teacher Shogi!*\n\nИзучай фигуры, решай задачи и проходи тесты.",
        parse_mode="Markdown", reply_markup=main_menu_keyboard()
    )

async def guide_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📖 *Изучение фигур*:", parse_mode="Markdown", reply_markup=pieces_menu_keyboard())

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["quiz_index"] = 0
    context.user_data["quiz_score"] = 0
    await send_quiz_message(update.message, context, is_edit=False)

async def puzzle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["puzzle_index"] = 0
    await send_puzzle_message(update.message, context, is_edit=False)

# ==================== ОБРАБОТЧИК КНОПОК ====================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "menu_main":
        try: await query.message.delete()
        except: pass
        await query.message.chat.send_message("🎌 *Главное меню*:", parse_mode="Markdown", reply_markup=main_menu_keyboard())

    elif data == "menu_pieces":
        await query.edit_message_text("📖 *Выберите фигуру:*", parse_mode="Markdown", reply_markup=pieces_menu_keyboard())

    elif data.startswith("piece_"):
        key = data.replace("piece_", "")
        piece = PIECES.get(key)
        if piece:
            text = f"*{piece['emoji']} {piece['name']}*\n\n{piece['description']}"
            media = []
            if os.path.exists(piece["img_main"]):
                media.append(InputMediaPhoto(open(piece["img_main"], "rb"), caption=text, parse_mode="Markdown"))
            if piece["img_promoted"] and os.path.exists(piece["img_promoted"]):
                media.append(InputMediaPhoto(open(piece["img_promoted"], "rb")))
            if media:
                try: await query.message.delete()
                except: pass
                await query.message.chat.send_media_group(media=media)
                await query.message.chat.send_message("🧭 Навигация:", reply_markup=back_to_main())

    elif data == "menu_quiz":
        context.user_data["quiz_index"] = 0
        context.user_data["quiz_score"] = 0
        await send_quiz_message(query, context, is_edit=True)

    elif data.startswith("quiz_ans_"):
        chosen = int(data.split("_")[2])
        idx = context.user_data.get("quiz_index", 0)
        quiz = QUIZZES[idx]
        if chosen == quiz["answer"]:
            context.user_data["quiz_score"] = context.user_data.get("quiz_score", 0) + 1
            res = "✅ *Верно!*"
        else:
            res = f"❌ *Неверно.* Правильный ответ: {quiz['options'][quiz['answer']]}"
        
        idx += 1
        context.user_data["quiz_index"] = idx
        keyboard = []
        if idx < len(QUIZZES):
            keyboard.append([InlineKeyboardButton("➡️ Следующий вопрос", callback_data="quiz_next")])
        else:
            res += f"\n\n🏁 Тест окончен! Результат: {context.user_data['quiz_score']}/{len(QUIZZES)}"
        keyboard.append([InlineKeyboardButton("🏠 Меню", callback_data="menu_main")])
        await query.edit_message_text(res, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "quiz_next":
        await send_quiz_message(query, context, is_edit=True)

    elif data == "menu_puzzles":
        context.user_data["puzzle_index"] = 0
        await send_puzzle_message(query, context, is_edit=True)

    elif data.startswith("puzzle_ans_"):
        chosen = int(data.split("_")[2])
        idx = context.user_data.get("puzzle_index", 0)
        puzzle = PUZZLES[idx]
        if chosen == puzzle["answer"]:
            res = f"✅ *Правильно!*\n\n{puzzle['explanation']}"
        else:
            res = f"❌ *Неверно.* {puzzle['explanation']}"
        
        idx += 1
        context.user_data["puzzle_index"] = idx
        keyboard = []
        if idx < len(PUZZLES):
            keyboard.append([InlineKeyboardButton("➡️ Следующая задача", callback_data="puzzle_next")])
        keyboard.append([InlineKeyboardButton("🏠 Меню", callback_data="menu_main")])
        await query.edit_message_caption(caption=res, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "puzzle_next":
        await send_puzzle_message(query, context, is_edit=True)

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
async def send_quiz_message(query_or_msg, context, is_edit):
    idx = context.user_data.get("quiz_index", 0)
    quiz = QUIZZES[idx]
    text = f"🧠 *Вопрос {idx + 1}/{len(QUIZZES)}*\n\n{quiz['question']}"
    kb = [[InlineKeyboardButton(opt, callback_data=f"quiz_ans_{i}")] for i, opt in enumerate(quiz["options"])]
    kb.append([InlineKeyboardButton("🏠 Меню", callback_data="menu_main")])
    if is_edit: await query_or_msg.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
    else: await query_or_msg.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def send_puzzle_message(query_or_msg, context, is_edit):
    idx = context.user_data.get("puzzle_index", 0)
    puzzle = PUZZLES[idx]
    text = f"♟ *Задача {idx + 1}/{len(PUZZLES)}*\n\n{puzzle['description']}"
    kb = [[InlineKeyboardButton(opt, callback_data=f"puzzle_ans_{i}")] for i, opt in enumerate(puzzle["options"])]
    kb.append([InlineKeyboardButton("🏠 Меню", callback_data="menu_main")])
    
    if os.path.exists(puzzle["image"]):
        if is_edit:
            try: await query_or_msg.message.delete()
            except: pass
            await query_or_msg.message.chat.send_photo(photo=open(puzzle["image"], "rb"), caption=text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
        else:
            await query_or_msg.reply_photo(photo=open(puzzle["image"], "rb"), caption=text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
    else:
        await query_or_msg.message.chat.send_message(f"⚠️ Ошибка: файл {puzzle['image']} не найден.")

async def post_init(application):
    await application.bot.set_my_commands([
        BotCommand("start", "Главное меню"),
        BotCommand("guide", "Изучение фигур"),
        BotCommand("test", "Пройти тест"),
        BotCommand("puzzle", "Задачи на ход"),
    ])

def main():
    app = Application.builder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("guide", guide_command))
    app.add_handler(CommandHandler("test", test_command))
    app.add_handler(CommandHandler("puzzle", puzzle_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == "__main__": main()

```
