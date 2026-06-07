import logging
import io
import os
from PIL import Image, ImageDraw, ImageFont
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# ==================== НАСТРОЙКИ ====================
# ⚠️ ОБЯЗАТЕЛЬНО СБРОСЬ ТОКЕН В @BotFather И ВСТАВЬ НОВЫЙ СЮДА!
TOKEN = "ТВОЙ_НОВЫЙ_ТОКЕН_БОТА"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== ГЕНЕРАЦИЯ ДОСКИ ====================
def draw_shogi_board(board, cols, rows, title=""):
    """
    board — словарь {(col, row): ("символ", "white"/"black")}
    cols, rows — размер видимой части доски
    """
    CELL = 100
    PADDING = 55
    HEADER = 55 if title else 15

    width = CELL * cols + PADDING * 2
    height = CELL * rows + PADDING * 2 + HEADER

    img = Image.new("RGB", (width, height), color=(255, 248, 220))
    draw = ImageDraw.Draw(img)

    # Попытка загрузить стандартные шрифты (работает на Windows/Linux при наличии)
    try:
        font_piece = ImageFont.truetype("arial.ttf", 30)
        font_label = ImageFont.truetype("arial.ttf", 20)
        font_title = ImageFont.truetype("arial.ttf", 24)
    except Exception:
        font_piece = ImageFont.load_default()
        font_label = ImageFont.load_default()
        font_title = ImageFont.load_default()

    if title:
        draw.text((width // 2, 28), title, fill=(80, 40, 0), font=font_title, anchor="mm")

    col_labels = ["а", "б", "в", "г", "д", "е", "ж", "з", "и"]
    for c in range(cols):
        x = PADDING + c * CELL + CELL // 2
        y = HEADER + PADDING - 25
        draw.text((x, y), col_labels[c], fill=(100, 60, 0), font=font_label, anchor="mm")

    for r in range(rows):
        x = PADDING - 25
        y = HEADER + PADDING + r * CELL + CELL // 2
        draw.text((x, y), str(r + 1), fill=(100, 60, 0), font=font_label, anchor="mm")

    for r in range(rows):
        for c in range(cols):
            x0 = PADDING + c * CELL
            y0 = HEADER + PADDING + r * CELL
            x1 = x0 + CELL
            y1 = y0 + CELL
            cell_color = (245, 222, 179) if (r + c) % 2 == 0 else (232, 208, 160)
            draw.rectangle([x0, y0, x1, y1], fill=cell_color, outline=(139, 90, 43), width=2)

            piece = board.get((c, r))
            if piece:
                symbol, side = piece
                cx = x0 + CELL // 2
                cy = y0 + CELL // 2
                circle_color = (255, 255, 255) if side == "white" else (50, 50, 50)
                draw.ellipse([cx - 36, cy - 36, cx + 36, cy + 36],
                             fill=circle_color, outline=(100, 60, 0), width=2)
                text_color = (30, 30, 30) if side == "white" else (220, 220, 220)
                draw.text((cx, cy), symbol, fill=text_color, font=font_piece, anchor="mm")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

# ==================== ДАННЫЕ О ФИГУРАХ ====================
# (Твой исходный словарь PIECES оставлен без изменений)
PIECES = {
    "ОУ": {
        "name": "Osho / Gyokusho (王将/玉将)",
        "ru_name": "Король",
        "emoji": "♔",
        "description": (
            "Самая главная фигура в сёги — Король.\n\n"
            "♟ Ход: на одну клетку в любом направлении (8 вариантов).\n"
            "🎯 Цель игры: поставить мат королю противника.\n"
            "⚠️ Особенность: не может ходить под шах.\n\n"
            "📜 Интересно: у старшего игрока фигура называется «Osho» (王将), "
            "у младшего — «Gyokusho» (玉将). По легенде, иероглиф с точкой (玉) "
            "получал более слабый игрок."
        ),
    },
    "ХИСЯ": {
        "name": "Hisha (飛車)",
        "ru_name": "Ладья",
        "emoji": "♜",
        "description": (
            "Hisha (飛車) — Ладья, одна из сильнейших фигур.\n\n"
            "♟ Ход: любое количество клеток по горизонтали или вертикали.\n"
            "⭐️ После превращения: становится «Ryuo» (龍王) — Король-дракон. "
            "Добавляется ход на одну клетку по диагонали.\n\n"
            "💡 Стратегия: ладью лучше держать в центре или на открытых вертикалях."
        ),
    },
    "КАКУ": {
        "name": "Kakugyo (角行)",
        "ru_name": "Слон",
        "emoji": "♗",
        "description": (
            "Kakugyo (角行) — Слон.\n\n"
            "♟ Ход: любое количество клеток по диагонали.\n"
            "⭐️ После превращения: становится «Ryuma» (龍馬) — Конь-дракон. "
            "Добавляется ход на одну клетку по горизонтали/вертикали.\n\n"
            "💡 Слон контролирует длинные диагонали и опасен в миттельшпиле."
        ),
    },
    "КИН": {
        "name": "Kinsho (金将)",
        "ru_name": "Золотой генерал",
        "emoji": "🥇",
        "description": (
            "Kinsho (金将) — Золотой генерал.\n\n"
            "♟ Ход: одна клетка — вперёд, назад, влево, вправо, "
            "или вперёд по диагонали (6 направлений).\n"
            "⚠️ Не превращается.\n\n"
            "💡 Золотой генерал — ключевая оборонительная фигура. "
            "Используется для построения крепкой защиты (крепость «Мино» и др.)."
        ),
    },
    "ГИН": {
        "name": "Ginsho (銀将)",
        "ru_name": "Серебряный генерал",
        "emoji": "🥈",
        "description": (
            "Ginsho (銀将) — Серебряный генерал.\n\n"
            "♟ Ход: одна клетка — вперёд, или по диагонали в любую сторону (5 направлений).\n"
            "⭐️ После превращения: ходит как Золотой генерал.\n\n"
            "💡 Серебряный генерал гибок в атаке. Часто продвигается вперёд "
            "для поддержки наступления."
        ),
    },
    "КЭЙ": {
        "name": "Keima (桂馬)",
        "ru_name": "Конь",
        "emoji": "♞",
        "description": (
            "Keima (桂馬) — Конь.\n\n"
            "♟ Ход: прыжок — на две клетки вперёд и одну в сторону "
            "(только вперёд! в отличие от шахматного коня).\n"
            "⭐️ После превращения: ходит как Золотой генерал.\n\n"
            "⚠️ Конь не может ходить с последних двух рядов — "
            "там его необходимо превратить."
        ),
    },
    "КЁ": {
        "name": "Kyosha (香車)",
        "ru_name": "Копьеносец",
        "emoji": "🏹",
        "description": (
            "Kyosha (香車) — Копьеносец.\n\n"
            "♟ Ход: любое количество клеток только вперёд (как ладья, но только вперёд).\n"
            "⭐️ После превращения: ходит как Золотой генерал.\n\n"
            "💡 Копьеносец стоит в углах доски в начале игры. "
            "Хорош для давления на вертикалях."
        ),
    },
    "ФУ": {
        "name": "Fuhyo (歩兵)",
        "ru_name": "Пешка",
        "emoji": "♟",
        "description": (
            "Fuhyo (歩兵) — Пешка.\n\n"
            "♟ Ход: одна клетка вперёд.\n"
            "⭐️ После превращения: становится «Tokin» (と金) — ходит как Золотой генерал.\n\n"
            "⚠️ Нельзя ставить две пешки на одной вертикали.\n"
            "⚠️ Нельзя ставить пешку с немедленным матом («утифу»).\n\n"
            "💡 Пешек 9 штук — больше всего. Превращённая пешка «Tokin» "
            "очень сильна и опасна для короля."
        ),
    },
}

# ==================== ТЕСТЫ ====================
# (Твой исходный массив QUIZZES оставлен без изменений)
QUIZZES = [
    {
        "question": "Какая фигура в сёги ходит только вперёд на любое количество клеток?",
        "options": ["Ладья (Hisha)", "Копьеносец (Kyosha)", "Конь (Keima)", "Пешка (Fuhyo)"],
        "answer": 1,
        "explanation": "Копьеносец (Kyosha) ходит только вперёд на любое количество клеток — как ладья, но только в одном направлении."
    },
    {
        "question": "Как называется превращённая Ладья (Hisha)?",
        "options": ["Ryuma (龍馬)", "Tokin (と金)", "Ryuo (龍王)", "Narikin"],
        "answer": 2,
        "explanation": "Превращённая Ладья называется Ryuo (龍王) — Король-дракон. Она добавляет ход по диагонали."
    },
    {
        "question": "Сколько пешек (Fuhyo) у каждого игрока в начале игры?",
        "options": ["7", "8", "9", "10"],
        "answer": 2,
        "explanation": "У каждого игрока 9 пешек — это самая многочисленная фигура в сёги."
    },
    {
        "question": "Какая фигура в сёги НЕ может превращаться?",
        "options": ["Серебряный генерал", "Золотой генерал", "Конь", "Копьеносец"],
        "answer": 1,
        "explanation": "Золотой генерал (Kinsho) — единственная фигура кроме Короля, которая не превращается."
    },
    {
        "question": "Что происходит с захваченными фигурами в сёги?",
        "options": [
            "Они убираются из игры",
            "Игрок может вернуть их на доску как свои",
            "Они ставятся рядом с доской для счёта",
            "Противник может их использовать"
        ],
        "answer": 1,
        "explanation": "Главная особенность сёги: захваченные фигуры переходят к захватившему и могут быть поставлены на доску как свои — это называется «сброс»."
    },
    {
        "question": "Как ходит Конь (Keima) в сёги?",
        "options": [
            "Как в обычных шахматах — буквой Г в любую сторону",
            "Только назад на одну клетку",
            "На две клетки вперёд и одну в сторону (только вперёд)",
            "По диагонали на две клетки"
        ],
        "answer": 2,
        "explanation": "Конь в сёги прыгает только вперёд: 2 клетки вперёд + 1 в сторону. В отличие от шахматного коня, он не может ходить назад или в стороны."
    },
    {
        "question": "Что такое «Tokin»?",
        "options": [
            "Превращённый Конь",
            "Превращённая Пешка",
            "Превращённый Копьеносец",
            "Особый тип Короля"
        ],
        "answer": 1,
        "explanation": "Tokin (と金) — превращённая пешка. После достижения зоны превращения пешка начинает ходить как Золотой генерал. Это очень сильная фигура!"
    },
    {
        "question": "В каком ряду начинает игру Ладья (Hisha)?",
        "options": ["В первом ряду", "Во втором ряду", "В третьем ряду", "В центре доски"],
        "answer": 1,
        "explanation": "Ладья стоит во втором ряду (справа), рядом со Слоном. Второй ряд — это ряд сильных фигур: Ладья и Слон."
    },
]

# ==================== ЗАДАЧИ ====================
# (Твой исходный массив PUZZLES оставлен без изменений)
PUZZLES = [
    {
        "title": "Задача 1: Запрещённый мат",
        "description": (
            "Пешка белых стоит на б2, Король чёрных на б1.\n\n"
            "❓ Что произойдёт если пешка сбросом встанет на б1?"
        ),
        "board": {
            (1, 0): ("王", "black"),
            (1, 1): ("歩", "white"),
        },
        "cols": 3, "rows": 3,
        "options": [
            "Пешка съест Короля — победа!",
            "Это запрещённый ход (утифу) — мат пешкой запрещён",
            "Пешка превратится в Tokin",
            "Ничего особенного"
        ],
        "answer": 1,
        "explanation": (
            "Правильно! Это «утифу» — запрещённый мат пешкой.\n"
            "В сёги нельзя ставить пешку сбросом так, чтобы это был немедленный мат. "
            "Это одно из важнейших особых правил!"
        )
    },
    {
        "title": "Задача 2: Защита сбросом",
        "description": (
            "Противник атакует твоего Короля (белые, б3) по вертикали «б».\n"
            "Ладья чёрных стоит на б1. У тебя есть захваченный Золотой генерал.\n\n"
            "❓ Как лучше защититься?"
        ),
        "board": {
            (1, 0): ("飛", "black"),
            (1, 2): ("王", "white"),
        },
        "cols": 3, "rows": 3,
        "options": [
            "Убежать Королём в сторону",
            "Сбросить Золотого генерала между Королём и ладьёй (б2)",
            "Атаковать чужого Короля",
            "Ничего не делать"
        ],
        "answer": 1,
        "explanation": (
            "Верно! Сброс Золотого генерала на б2 блокирует атаку ладьи — "
            "классическая защитная техника в сёги.\n"
            "Захваченные фигуры можно использовать для защиты в нужный момент!"
        )
    },
    {
        "title": "Задача 3: Превращение пешки",
        "description": (
            "Пешка белых дошла до последнего (1-го) ряда — позиция б1.\n\n"
            "❓ Что должно произойти?"
        ),
        "board": {
            (1, 0): ("歩", "white"),
        },
        "cols": 3, "rows": 3,
        "options": [
            "Пешка остаётся пешкой — ничего не происходит",
            "Пешка обязана превратиться в Tokin",
            "Можно выбрать: превратить или нет",
            "Пешка убирается с доски"
        ],
        "answer": 1,
        "explanation": (
            "Правильно! Пешка на letzten ряду обязана превратиться, "
            "так как у неё нет допустимого хода вперёд.\n"
            "Она превращается в Tokin (と金) и начинает ходить как Золотой генерал."
        )
    },
]

# ==================== КЛАВИАТУРЫ ====================
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📖 Изучить фигуры", callback_data="menu_pieces")],
        [InlineKeyboardButton("🧠 Пройти тест", callback_data="menu_quiz")],
        [InlineKeyboardButton("♟ Задачи на ход", callback_data="menu_puzzles")],
        [InlineKeyboardButton("📜 Правила игры", callback_data="menu_rules")],
        [InlineKeyboardButton("ℹ️ О сёги", callback_data="menu_about")],
    ]
    return InlineKeyboardMarkup(keyboard)

def pieces_menu_keyboard():
    keyboard = []
    for key, piece in PIECES.items():
        btn_text = f"{piece['emoji']} {piece['ru_name']} ({piece['name'].split(' ')[0]})"
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
    text = (
        "🎌 *Добро пожаловать в обучающий бот по Сёги!*\n\n"
        "将棋 — японские шахматы, одна из древнейших стратегических игр мира.\n\n"
        "Здесь ты можешь:\n"
        "📖 Изучить все фигуры и их ходы\n"
        "🧠 Проверить знания в тестах\n"
        "♟ Решить задачи на лучший ход\n\n"
        "Выбери раздел или используй команды:\n"
        "/guide — обучение фигурам\n"
        "/test — пройти тест\n"
        "/puzzle — задачи на ход\n"
        "/help — помощь"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_menu_keyboard())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📚 *Помощь*\n\n"
        "Доступные команды:\n\n"
        "/start — Главное меню\n"
        "/guide — Изучение фигур\n"
        "/test — Пройти тест по сёги\n"
        "/puzzle — Задачи на лучший ход\n"
        "/help — Это сообщение\n\n"
        "Также можно нажимать кнопки в меню 👆"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_menu_keyboard())

async def guide_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *Изучение фигур*\n\nВыбери фигуру:",
        parse_mode="Markdown",
        reply_markup=pieces_menu_keyboard()
    )

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["quiz_index"] = 0
    context.user_data["quiz_score"] = 0
    q = QUIZZES[0]
    text = f"🧠 *Вопрос 1/{len(QUIZZES)}*\n\n{q['question']}"
    keyboard = []
    for i, option in enumerate(q["options"]):
        keyboard.append([InlineKeyboardButton(option, callback_data=f"quiz_ans_{i}")])
    keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")])
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def puzzle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["puzzle_index"] = 0
    await send_puzzle_new_message(update.message, context)

# ==================== ОБРАБОТЧИК КНОПОК ====================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "menu_main":
        is_photo = context.user_data.get("last_is_photo", False)
        context.user_data.clear()
        if is_photo:
            try:
                await query.message.delete()
            except Exception:
                pass
            await query.message.chat.send_message(
                "🎌 *Главное меню*\n\nВыбери раздел:",
                parse_mode="Markdown",
                reply_markup=main_menu_keyboard()
            )
        else:
            try:
                await query.edit_message_text(
                    "🎌 *Главное меню*\n\nВыбери раздел:",
                    parse_mode="Markdown",
                    reply_markup=main_menu_keyboard()
                )
            except Exception:
                try:
                    await query.message.delete()
                except Exception:
                    pass
                await query.message.chat.send_message(
                    "🎌 *Главное меню*\n\nВыбери раздел:",
                    parse_mode="Markdown",
                    reply_markup=main_menu_keyboard()
                )

    elif data == "menu_pieces":
        await query.edit_message_text(
            "📖 *Фигуры сёги*\n\nВыбери фигуру, чтобы узнать о ней подробнее:",
            parse_mode="Markdown",
            reply_markup=pieces_menu_keyboard()
        )

    elif data.startswith("piece_"):
        key = data.replace("piece_", "")
        piece = PIECES.get(key)
        if piece:
            text = f"*{piece['emoji']} {piece['name']}*\n*Русское название: {piece['ru_name']}*\n\n{piece['description']}"
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_to_main())

    elif data == "menu_quiz":
        context.user_data["quiz_index"] = 0
        context.user_data["quiz_score"] = 0
        await send_quiz_message(query, context)

    elif data.startswith("quiz_ans_"):
        chosen = int(data.split("_")[2])
        q_index = context.user_data.get("quiz_index", 0)
        quiz = QUIZZES[q_index]
        correct = quiz["answer"]
        score = context.user_data.get("quiz_score", 0)

        if chosen == correct:
            result_text = f"✅ *Верно!*\n\n{quiz['explanation']}"
            context.user_data["quiz_score"] = score + 1
        else:
            result_text = (
                f"❌ *Неверно.*\n"
                f"Ты выбрал: «{quiz['options'][chosen]}»\n"
                f"Правильный ответ: «{quiz['options'][correct]}»\n\n"
                f"{quiz['explanation']}"
            )

        next_index = q_index + 1
        context.user_data["quiz_index"] = next_index

        if next_index < len(QUIZZES):
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"➡️ Вопрос {next_index + 1}/{len(QUIZZES)}", callback_data="quiz_next")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")]
            ])
        else:
            final_score = context.user_data.get("quiz_score", 0)
            total = len(QUIZZES)
            result_text += f"\n\n🏁 *Тест завершён!*\nТвой результат: *{final_score}/{total}*"
            if final_score == total:
                result_text += "\n🏆 Отлично! Ты знаешь сёги!"
            elif final_score >= total * 0.7:
                result_text += "\n👍 Хороший результат! Продолжай изучение."
            else:
                result_text += "\n📖 Рекомендую ещё раз изучить фигуры."
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Пройти ещё раз", callback_data="menu_quiz")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")]
            ])

        await query.edit_message_text(result_text, parse_mode="Markdown", reply_markup=keyboard)

    elif data == "quiz_next":
        await send_quiz_message(query, context)

    elif data == "quiz_prev":
        context.user_data["quiz_index"] = max(0, context.user_data.get("quiz_index", 1) - 1)
        await send_quiz_message(query, context)

    elif data == "menu_puzzles":
        context.user_data["puzzle_index"] = 0
        await send_puzzle_edit(query, context)

    elif data.startswith("puzzle_ans_"):
        chosen = int(data.split("_")[2])
        p_index = context.user_data.get("puzzle_index", 0)
        if p_index >= len(PUZZLES):
            p_index = 0
            context.user_data["puzzle_index"] = 0
        puzzle = PUZZLES[p_index]
        correct = puzzle["answer"]

        if chosen == correct:
            result_text = f"✅ *Правильно!*\n\n{puzzle['explanation']}"
        else:
            result_text = (
                f"❌ *Не совсем.*\n"
                f"Правильный ответ: «{puzzle['options'][correct]}»\n\n"
                f"{puzzle['explanation']}"
            )

        next_index = p_index + 1
        context.user_data["puzzle_index"] = next_index
        
        if next_index < len(PUZZLES):
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"➡️ Задача {next_index + 1}/{len(PUZZLES)}", callback_data="puzzle_next")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")]
            ])
        else:
            result_text += "\n\n🏁 *Все задачи решены! Молодец!*"
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Решить ещё раз", callback_data="menu_puzzles")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")]
            ])

        # После фото редактируем подпись
        try:
            await query.edit_message_caption(caption=result_text, parse_mode="Markdown", reply_markup=keyboard)
        except Exception:
            try:
                await query.edit_message_text(result_text, parse_mode="Markdown", reply_markup=keyboard)
            except Exception:
                await query.message.reply_text(result_text, parse_mode="Markdown", reply_markup=keyboard)
        # Запоминаем, что текущее сообщение — подпись к фото
        context.user_data["last_is_photo"] = True

    elif data == "puzzle_next":
        await send_puzzle_edit(query, context)

    elif data == "puzzle_prev":
        context.user_data["puzzle_index"] = max(0, context.user_data.get("puzzle_index", 1) - 1)
        await send_puzzle_edit(query, context)

    elif data == "menu_rules":
        rules_text = (
            "📜 *Основные правила Сёги*\n\n"
            "🎯 *Цель:* поставить мат Королю противника.\n\n"
            "🗺 *Доска:* 9×9 клеток. Каждый игрок начинает с 20 фигурами.\n\n"
            "🔄 *Зона превращения:* три последних ряда противника.\n"
            "Большинство фигур могут превратиться, достигнув этой зоны.\n\n"
            "♻️ *Сброс (главная особенность!):*\n"
            "Захваченные фигуры переходят к тебе.\n"
            "Ты можешь в свой ход поставить захваченную фигуру "
            "на любую свободную клетку доски вместо обычного хода.\n\n"
            "⛔️ *Запреты при сбросе:*\n"
            "• Нельзя ставить пешку на вертикаль, где уже есть своя пешка\n"
            "• Нельзя ставить пешку с немедленным матом (утифу)\n"
            "• Нельзя ставить фигуру туда, где у неё нет ходов\n\n"
            "🏳️ *Ничья:* возможна при повторении позиции 4 раза."
        )
        await query.edit_message_text(rules_text, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="menu_main")]]))

    elif data == "menu_about":
        about_text = (
            "ℹ️ *О сёги (将棋)*\n\n"
            "Сёги — японская стратегическая игра, родственная шахматам.\n\n"
            "📅 *История:*\n"
            "Игра появилась в Японии около XII века.\n"
            "Произошла от индийской чатуранги через китайские шахматы сянци.\n\n"
            "🌏 *Популярность:*\n"
            "В Японии около 20 миллионов игроков.\n"
            "Существует профессиональная лига с титулами: Мейдзин, Рюо и др.\n\n"
            "🤖 *Компьютер vs человек:*\n"
            "С 2013 года компьютерные программы стабильно превосходят "
            "профессиональных игроков.\n\n"
            "🎌 *Уникальность:*\n"
            "Главное отличие от шахмат — сброс захваченных фигур.\n"
            "Это делает партии более динамичными и сложными."
        )
        await query.edit_message_text(about_text, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="menu_main")]]))

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
async def send_quiz_message(query, context):
    q_index = context.user_data.get("quiz_index", 0)
    quiz = QUIZZES[q_index]
    total = len(QUIZZES)
    text = f"🧠 *Вопрос {q_index + 1}/{total}*\n\n{quiz['question']}"
    keyboard = []
    for i, option in enumerate(quiz["options"]):
        keyboard.append([InlineKeyboardButton(option, callback_data=f"quiz_ans_{i}")])
    nav_row = []
    if q_index > 0:
        nav_row.append(InlineKeyboardButton("◀️ Назад", callback_data="quiz_prev"))
    nav_row.append(InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main"))
    keyboard.append(nav_row)
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def send_puzzle_edit(query, context):
    """Отправляет задачу с картинкой доски (редактирует сообщение на текст + новое фото)"""
    p_index = context.user_data.get("puzzle_index", 0)
    puzzle = PUZZLES[p_index]
    total = len(PUZZLES)

    # Генерируем картинку доски
    board_img = draw_shogi_board(
        puzzle["board"], puzzle["cols"], puzzle["rows"], title=puzzle["title"]
    )

    keyboard = []
    for i, option in enumerate(puzzle["options"]):
        keyboard.append([InlineKeyboardButton(option, callback_data=f"puzzle_ans_{i}")])
    nav_row = []
    if p_index > 0:
        nav_row.append(InlineKeyboardButton("◀️ Назад", callback_data="puzzle_prev"))
    nav_row.append(InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main"))
    keyboard.append(nav_row)
    markup = InlineKeyboardMarkup(keyboard)

    caption = f"♟ *Задача {p_index + 1}/{total}*\n\n{puzzle['description']}"

    # Удаляем старое сообщение и отправляем новое с фото
    try:
        await query.message.delete()
    except Exception:
        pass
    await query.message.chat.send_photo(
        photo=board_img,
        caption=caption,
        parse_mode="Markdown",
        reply_markup=markup
    )

async def send_puzzle_new_message(message, context):
    """Отправляет первую задачу новым сообщением"""
    p_index = context.user_data.get("puzzle_index", 0)
    puzzle = PUZZLES[p_index]
    total = len(PUZZLES)

    board_img = draw_shogi_board(
        puzzle["board"], puzzle["cols"], puzzle["rows"], title=puzzle["title"]
    )

    keyboard = []
    for i, option in enumerate(puzzle["options"]):
        keyboard.append([InlineKeyboardButton(option, callback_data=f"puzzle_ans_{i}")])
    keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")])
    markup = InlineKeyboardMarkup(keyboard)

    caption = f"♟ *Задача {p_index + 1}/{total}*\n\n{puzzle['description']}"
    await message.reply_photo(photo=board_img, caption=caption, parse_mode="Markdown", reply_markup=markup)

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Используй /start для начала или выбери раздел 🎌",
        reply_markup=main_menu_keyboard()
    )

# ==================== ЗАПУСК ====================
async def post_init(application):
    await application.bot.set_my_commands([
        BotCommand("start", "Главное меню"),
        BotCommand("guide", "Изучение фигур"),
        BotCommand("test", "Пройти тест"),
        BotCommand("puzzle", "Задачи на ход"),
        BotCommand("help", "Помощь"),
    ])

def main():
    app = Application.builder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("guide", guide_command))
    app.add_handler(CommandHandler("test", test_command))
    app.add_handler(CommandHandler("puzzle", puzzle_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown))
    
    print("🎌 Бот Сёги запущен! Нажми Ctrl+C для остановки.")
    app.run_polling()

if __name__ == "__main__":
    main()
