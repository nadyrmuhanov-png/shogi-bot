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
            "⭐ *После превращения:* становится Лошадью («Ryuma»). Сохраняет ходы слона + добавляется ход на 1 клетку по вертикали/горизонтали."
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

# ==================== БАЗА ТЕСТОВ И ЗАДАЧ ====================
QUIZZES = [
    {
        "question": "Какая фигура в сёги ходит только вперёд на любое количество клеток?",
        "options": ["Ладья (Hisha)", "Копьеносец (Kyosha)", "Конь (Keima)", "Пешка (Fuhyo)"],
        "answer": 1,
        "explanation": "Копьеносец (Kyosha) бьет всю вертикаль строго перед собой."
    },
    {
        "question": "Как называется превращённая Ладья (Hisha)?",
        "options": ["Ryuma (龍馬)", "Tokin (と金)", "Ryuo (龍王)", "Narikin"],
        "answer": 2,
        "explanation": "Превращённая Ладья называется Король-дракон или Ryuo (龍王)."
    },
    {
        "question": "Какая из этих фигур НЕ может превратиться?",
        "options": ["Серебряный генерал", "Золотой генерал", "Конь", "Пешка"],
        "answer": 1,
        "explanation": "Золотой генерал (Kinsho) и Король — единственные базовые фигуры, которые изначально не имеют перевёрнутой стороны."
    },
    {
        "question": "Что такое «Утифу» (Uchifu)?",
        "options": ["Запрет иметь две пешки на одной вертикали", "Запрет ставить мат сбросом пешки", "Ход пешкой назад", "Превращение пешки"],
        "answer": 1,
        "explanation": "Утифу — это правило, запрещающее ставить мат Королю соперника непосредственным сбросом пешки с руки."
    }
]

TASKS = [
    {
        "title": "Задача 1: Поиск мата (Цумэ-сёги)",
        "description": "У вас на руке (в комидае) есть Золотой генерал (Кин). Король соперника зажат в углу на поле 1a. Куда эффективнее всего сбросить Золотого генерала, чтобы поставить чистый мат в 1 ход?",
        "options": ["Сбросить на 1b", "Сбросить на 2b", "Сбросить на 2a", "Пойти пешкой"],
        "answer": 0,
        "explanation": "Сброс Золотого генерала на 1b прямо перед Королем соперника отрезает ему все пути к отступлению и ставит мат (если его некому съесть)."
    },
    {
        "title": "Задача 2: Безопасный сброс пешки",
        "description": "На вертикали 2 уже стоит ваша непривращенная пешка. Можете ли вы сбросить еще одну пешку на эту же вертикаль 2?",
        "options": ["Да, без ограничений", "Да, если это ставит шах", "Нет, это правило Нифу (Две пешки)", "Нет, если соперник против"],
        "answer": 2,
        "explanation": "Правило Нифу (Nifu) строго запрещает иметь две свои непривращенные пешки на одной и той же вертикальной линии."
    }
]

# ==================== КЛАВИАТУРЫ ====================
def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 Изучить фигуры", callback_data="menu_pieces")],
        [InlineKeyboardButton("🧠 Пройти тест", callback_data="menu_quiz")],
        [InlineKeyboardButton("🧩 Задачи на ход", callback_data="menu_tasks")],
        [InlineKeyboardButton("📜 Правила игры", callback_data="menu_rules")],
        [InlineKeyboardButton("ℹ️ О сёги", callback_data="menu_about")]
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
        "🎌 *Добро пожаловать в Teacher Shogi!*\n\nТвой личный интерактивный тренер по японским шахматам. Выбери раздел меню ниже:",
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

            if os.path.exists(piece["img_main"]):
                media_group.append(InputMediaPhoto(open(piece["img_main"], "rb"), caption=caption_text, parse_mode="Markdown"))
            
            if piece["img_promoted"] and os.path.exists(piece["img_promoted"]):
                media_group.append(InputMediaPhoto(open(piece["img_promoted"], "rb")))

            if media_group:
                try:
                    await query.message.delete()
                except Exception:
                    pass
                await query.message.chat.send_media_group(media=media_group)
                await query.message.chat.send_message("🧭 Навигация:", reply_markup=back_to_main())
            else:
                missing_files = piece["img_main"]
                if piece["img_promoted"]:
                    missing_files += f" или {piece['img_promoted']}"
                await query.message.chat.send_message(f"⚠️ Ошибка: На GitHub не найден файл `{missing_files}`.")

    # --- ЛОГИКА ТЕСТОВ (QUIZ) ---
    elif data == "menu_quiz":
        context.user_data["quiz_index"] = 0
        context.user_data["quiz_score"] = 0
        await send_quiz_message(query, context)

    elif data.startswith("quiz_ans_"):
        chosen = int(data.split("_")[2])
        idx = context.user_data.get("quiz_index", 0)
        quiz = QUIZZES[idx]
        
        if chosen == quiz["answer"]:
            context.user_data["quiz_score"] = context.user_data.get("quiz_score", 0) + 1
            res = "✅ *Правильно!*"
        else:
            res = f"❌ *Неверно!*\nПравильный ответ: {quiz['options'][quiz['answer']]}"
            
        res += f"\n\n💡 {quiz['explanation']}"
        context.user_data["quiz_index"] = idx + 1
        
        keyboard = []
        if context.user_data["quiz_index"] < len(QUIZZES):
            keyboard.append([InlineKeyboardButton("➡️ Следующий вопрос", callback_data="quiz_next")])
        else:
            res += f"\n\n🏁 *Тест окончен!*\nТвой результат: {context.user_data['quiz_score']}/{len(QUIZZES)}"
        keyboard.append([InlineKeyboardButton("🏠 В меню", callback_data="menu_main")])
        
        await query.edit_message_text(res, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "quiz_next":
        await send_quiz_message(query, context)

    # --- ЛОГИКА ЗАДАЧ (TASKS) ---
    elif data == "menu_tasks":
        context.user_data["task_index"] = 0
        await send_task_message(query, context)

    elif data.startswith("task_ans_"):
        chosen = int(data.split("_")[2])
        idx = context.user_data.get("task_index", 0)
        task = TASKS[idx]
        
        if chosen == task["answer"]:
            res = "🎉 *Великолепно! Решение верное.*"
        else:
            res = f"⚠️ *Мимо.*\nВерный ход: {task['options'][task['answer']]}"
            
        res += f"\n\n📘 *Разбор тактики:* {task['explanation']}"
        context.user_data["task_index"] = idx + 1
        
        keyboard = []
        if context.user_data["task_index"] < len(TASKS):
            keyboard.append([InlineKeyboardButton("🧩 Следующая задача", callback_data="task_next")])
        else:
            res += "\n\n🏆 Все доступные тактические задачи решены!"
        keyboard.append([InlineKeyboardButton("🏠 В меню", callback_data="menu_main")])
        
        await query.edit_message_text(res, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "task_next":
        await send_task_message(query, context)

    # --- ИНФОРМАЦИОННЫЕ ПАНЕЛИ ---
    elif data == "menu_rules":
        rules_text = (
            "📜 *Базовый кодекс Сёги:*\n\n"
            "1. Поле боя имеет размер 9х9 клеток.\n"
            "2. Главная цель игры — объявить мат Королю противника.\n"
            "3. Уникальное свойство («Сброс»): фигуры, которые вы забираете у соперника, не уходят до конца игры. Их можно выставить из резерва (с руки) обратно на любую клетку поля вместо очередного хода!"
        )
        await query.edit_message_text(rules_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="menu_main")]]))

    elif data == "menu_about":
        about_text = (
            "ℹ️ *О проекте Teacher Shogi:*\n\n"
            "Этот бот разработан, чтобы помочь новичкам быстро освоить каллиграфию японских шахмат, понять направления ходов сложных генералов и отточить мастерство на цумэ-задачах.\n\n"
            "Удачи в обучении, Сёги — игра великих стратегов! 🎌"
        )
        await query.edit_message_text(about_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="menu_main")]]))

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ МЕНЮ ====================
async def send_quiz_message(query, context):
    idx = context.user_data.get("quiz_index", 0)
    quiz = QUIZZES[idx]
    text = f"🧠 *Вопрос {idx + 1}/{len(QUIZZES)}:*\n\n{quiz['question']}"
    keyboard = [[InlineKeyboardButton(opt, callback_data=f"quiz_ans_{i}")] for i, opt in enumerate(quiz["options"])]
    keyboard.append([InlineKeyboardButton("🏠 Выйти в меню", callback_data="menu_main")])
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def send_task_message(query, context):
    idx = context.user_data.get("task_index", 0)
    task = TASKS[idx]
    text = f"🧩 *{task['title']}*\n\n{task['description']}"
    keyboard = [[InlineKeyboardButton(opt, callback_data=f"task_ans_{i}")] for i, opt in enumerate(task["options"])]
    keyboard.append([InlineKeyboardButton("🏠 Выйти в меню", callback_data="menu_main")])
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("🎌 Полная версия Teacher Shogi успешно запущена!")
    app.run_polling()

if __name__ == "__main__":
    main()
