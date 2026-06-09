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
TOKEN = "8999275602:AAHW3Od88rtO5f_JEgxpoa-sB3FlScEneTE"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Имя файла шрифта, который должен лежать в корне проекта на GitHub/Railway
FONT_FILE = "shogi_font.ttc"

def get_font(size):
    """Безопасно загружает шрифт из корня проекта или откатывается на дефолт"""
    try:
        if os.path.exists(FONT_FILE):
            return ImageFont.truetype(FONT_FILE, size)
    except Exception as e:
        logger.error(f"Ошибка загрузки кастомного шрифта {FONT_FILE}: {e}")
    return ImageFont.load_default()

# ==================== ГЕНЕРАЦИЯ ДОСКИ ====================
def draw_shogi_board(board, cols, rows, title=""):
    CELL = 100
    PADDING = 55
    HEADER = 55 if title else 15

    width = CELL * cols + PADDING * 2
    height = CELL * rows + PADDING * 2 + HEADER

    img = Image.new("RGB", (width, height), color=(255, 248, 220))
    draw = ImageDraw.Draw(img)

    font_piece = get_font(30)
    font_label = get_font(20)
    font_title = get_font(24)

    if title:
        try:
            draw.text((width // 2, 28), title, fill=(80, 40, 0), font=font_title, anchor="mm")
        except Exception:
            draw.text((width // 2, 10), title, fill=(80, 40, 0), font=font_title)

    col_labels = ["а", "б", "в", "г", "д", "е", "ж", "з", "и"]
    for c in range(cols):
        x = PADDING + c * CELL + CELL // 2
        y = HEADER + PADDING - 25
        try:
            draw.text((x, y), col_labels[c], fill=(100, 60, 0), font=font_label, anchor="mm")
        except Exception:
            draw.text((x, y), col_labels[c], fill=(100, 60, 0), font=font_label)

    for r in range(rows):
        x = PADDING - 25
        y = HEADER + PADDING + r * CELL + CELL // 2
        try:
            draw.text((x, y), str(r + 1), fill=(100, 60, 0), font=font_label, anchor="mm")
        except Exception:
            draw.text((x, y), str(r + 1), fill=(100, 60, 0), font=font_label)

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
                try:
                    draw.text((cx, cy), symbol, fill=text_color, font=font_piece, anchor="mm")
                except Exception:
                    draw.text((cx - 10, cy - 10), symbol, fill=text_color, font=font_piece)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

# ==================== ГЕНЕРАЦИЯ КАРТОЧКИ ФИГУРЫ ====================
def draw_piece_card(piece):
    """Генерирует пятиугольную карточку Кома с каноничными кандзи сторон"""
    W, H = 450, 480
    img = Image.new("RGB", (W, H), color=(245, 242, 235))
    draw = ImageDraw.Draw(img)

    font_big = get_font(110)
    font_mid = get_font(50)
    font_name = get_font(32)
    font_small = get_font(20)

    # Вершины традиционной пятиугольной фигуры сёги
    poly_points = [
        (W // 2, 40),      # Верхний пик
        (W - 80, 90),      # Верхний правый угол
        (W - 60, 290),     # Нижний правый угол
        (60, 290),         # Нижний левый угол
        (80, 90)           # Верхний левый угол
    ]
    
    try:
        # Эффект тени плашки
        shadow_points = [(p[0] + 4, p[1] + 5) for p in poly_points]
        draw.polygon(shadow_points, fill=(210, 205, 195))
        
        # Деревянная плашка фигуры
        draw.polygon(poly_points, fill=(242, 198, 124), outline=(139, 90, 43), width=4)

        cx = W // 2
        
        # Отрисовка сторон иероглифов (Кандзи)
        if piece.get("promoted_kanji"):
            draw.text((cx - 45, 175), piece["kanji"], font=font_big, fill=(30, 30, 30), anchor="mm")
            # Перевернутая сторона традиционно отображается темно-красным цветом
            draw.text((cx + 55, 185), piece["promoted_kanji"], font=font_mid, fill=(180, 30, 30), anchor="mm")
            draw.text((cx - 45, 85), "Основная", font=font_small, fill=(120, 90, 50), anchor="mm")
            draw.text((cx + 55, 115), "Перевернутая", font=font_small, fill=(150, 70, 70), anchor="mm")
        else:
            draw.text((cx, 170), piece["kanji"], font=font_big, fill=(30, 30, 30), anchor="mm")

        # Названия и футер
        draw.text((cx, 345), piece["name"], font=font_name, fill=(60, 30, 0), anchor="mm")
        
        ru_txt = f" {piece['ru_name']} "
        draw.rounded_rectangle([cx - 130, 380, cx + 130, 415], radius=5, fill=(225, 215, 195))
        draw.text((cx, 396), ru_txt, font=font_small, fill=(100, 40, 0), anchor="mm")
        draw.text((cx, 450), "将棋 • Japanese Chess", font=font_small, fill=(160, 140, 120), anchor="mm")
        
    except Exception as e:
        logger.error(f"Ошибка Pillow отрисовки (возможно, дефолтный шрифт): {e}")
        draw.text((W // 2, H // 2), piece["ru_name"], fill=(0, 0, 0), font=font_name, anchor="mm")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

# ==================== ДАННЫЕ О ФИГУРАХ ====================
PIECES = {
    "ОУ": {
        "name": "Osho / Gyokusho (王将/玉将)",
        "ru_name": "Король",
        "kanji": "王",
        "promoted_kanji": None,
        "description": (
            "Самая главная фигура в сёги — Король.\n\n"
            "♟ Ход: на одну клетку в любом направлении (8 вариантов).\n"
            "🎯 Цель игры: поставить мат королю противника.\n"
            "⚠️ Особенность: не может ходить под шах.\n\n"
            "📜 Интересно: у старшего игрока фигура называется «Osho» (王将), "
            "у младшего — «Gyokusho» (玉将)."
        ),
    },
    "ХИСЯ": {
        "name": "Hisha (飛車)",
        "ru_name": "Ладья",
        "kanji": "飛",
        "promoted_kanji": "龍",
        "description": (
            "Hisha (飛車) — Ладья, одна из сильнейших фигур.\n\n"
            "♟ Ход: любое количество клеток по горизонтали или вертикали.\n"
            "⭐ После превращения: становится «Ryuo» (龍王) — Король-дракон. "
            "Добавляется ход на одну клетку по диагонали."
        ),
    },
    "КАКУ": {
        "name": "Kakugyo (角行)",
        "ru_name": "Слон",
        "kanji": "角",
        "promoted_kanji": "馬",
        "description": (
            "Kakugyo (角行) — Слон.\n\n"
            "♟ Ход: любое количество клеток по диагонали.\n"
            "⭐ После превращения: становится «Ryuma» (龍馬) — Конь-дракон. "
            "Добавляется ход на одну клетку по горизонтали/вертикали."
        ),
    },
    "КИН": {
        "name": "Kinsho (金将)",
        "ru_name": "Золотой генерал",
        "kanji": "金",
        "promoted_kanji": None,
        "description": (
            "Kinsho (金将) — Золотой генерал.\n\n"
            "♟ Ход: одна клетка — вперёд, назад, влево, вправо, "
            "или вперёд по диагонали (6 направлений).\n"
            "⚠️ Не превращается."
        ),
    },
    "ГИН": {
        "name": "Ginsho (銀将)",
        "ru_name": "Серебряный генерал",
        "kanji": "銀",
        "promoted_kanji": "全",
        "description": (
            "Ginsho (銀将) — Серебряный генерал.\n\n"
            "♟ Ход: одна клетка — вперёд, или по диагонали в любую сторону (5 направлений).\n"
            "⭐ После превращения: ходит как Золотой генерал (иероглиф 全)."
        ),
    },
    "КЭЙ": {
        "name": "Keima (桂馬)",
        "ru_name": "Конь",
        "kanji": "桂",
        "promoted_kanji": "圭",
        "description": (
            "Keima (桂馬) — Конь.\n\n"
            "♟ Ход: прыжок — на две клетки вперёд и одну в сторону (только вперёд!).\n"
            "⭐ После превращения: ходит как Золотой генерал."
        ),
    },
    "КЁ": {
        "name": "Kyosha (香車)",
        "ru_name": "Копьеносец",
        "kanji": "香",
        "promoted_kanji": "杏",
        "description": (
            "Kyosha (香車) — Копьеносец.\n\n"
            "♟ Ход: любое количество клеток только вперёд.\n"
            "⭐ После превращения: ходит как Золотой генерал."
        ),
    },
    "ФУ": {
        "name": "Fuhyo (歩兵)",
        "ru_name": "Пешка",
        "kanji": "歩",
        "promoted_kanji": "と",
        "description": (
            "Fuhyo (歩兵) — Пешка.\n\n"
            "♟ Ход: одна клетка вперёд.\n"
            "⭐ После превращения: становится «Tokin» (と金) — ходит как Золотой генерал."
        ),
    },
}

# ==================== ТЕСТЫ И ЗАДАЧИ ====================
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

PUZZLES = [
    {
        "title": "Задача 1: Запрещённый мат",
        "description": "Пешка белых стоит на б2, Король чёрных на б1.\n\n❓ Что произойдёт если пешка сбросом встанет на б1?",
        "board": {(1, 0): ("王", "black"), (1, 1): ("歩", "white")},
        "cols": 3, "rows": 3,
        "options": [
            "Пешка съест Короля — победа!",
            "Это запрещённый ход (утифу) — мат пешкой запрещён",
            "Пешка превратится в Tokin",
            "Ничего особенного"
        ],
        "answer": 1,
        "explanation": "Правильно! Это «утифу» — запрещённый мат сбросом пешки."
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
        btn_text = f"{piece['kanji']} {piece['ru_name']}"
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
        "Выбери раздел меню ниже или используй команды:\n"
        "/guide — обучение фигурам\n"
        "/test — пройти тест\n"
        "/puzzle — задачи на ход"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_menu_keyboard())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Используй кнопки меню или /start для перезапуска.", reply_markup=main_menu_keyboard())

async def guide_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📖 *Изучение фигур*\n\nВыбери фигуру:", parse_mode="Markdown", reply_markup=pieces_menu_keyboard())

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["quiz_index"] = 0
    context.user_data["quiz_score"] = 0
    q = QUIZZES[0]
    text = f"🧠 *Вопрос 1/{len(QUIZZES)}*\n\n{q['question']}"
    keyboard = [[InlineKeyboardButton(opt, callback_data=f"quiz_ans_{i}")] for i, opt in enumerate(q["options"])]
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
            await query.message.chat.send_message("🎌 *Главное меню*:", parse_mode="Markdown", reply_markup=main_menu_keyboard())
        else:
            try:
                await query.edit_message_text("🎌 *Главное меню*:", parse_mode="Markdown", reply_markup=main_menu_keyboard())
            except Exception:
                await query.message.chat.send_message("🎌 *Главное меню*:", parse_mode="Markdown", reply_markup=main_menu_keyboard())

    elif data == "menu_pieces":
        context.user_data["last_is_photo"] = False
        try:
            await query.edit_message_text("📖 *Фигуры сёги*:", parse_mode="Markdown", reply_markup=pieces_menu_keyboard())
        except Exception:
            await query.message.chat.send_message("📖 *Фигуры сёги*:", parse_mode="Markdown", reply_markup=pieces_menu_keyboard())

    elif data.startswith("piece_"):
        key = data.replace("piece_", "")
        piece = PIECES.get(key)
        if piece:
            text = f"*{piece['kanji']} {piece['name']}*\n*Русское название: {piece['ru_name']}*\n\n{piece['description']}"
            piece_img = draw_piece_card(piece)
            try:
                await query.message.delete()
            except Exception:
                pass
            await query.message.chat.send_photo(
                photo=piece_img, caption=text, parse_mode="Markdown", reply_markup=back_to_main()
            )
            context.user_data["last_is_photo"] = True

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
            result_text = f"❌ *Неверно.*\nПравильный ответ: «{quiz['options'][correct]}»\n\n{quiz['explanation']}"

        next_index = q_index + 1
        context.user_data["quiz_index"] = next_index

        if next_index < len(QUIZZES):
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"➡️ Вопрос {next_index + 1}", callback_data="quiz_next")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")]
            ])
        else:
            final_score = context.user_data.get("quiz_score", 0)
            result_text += f"\n\n🏁 *Тест завершён!*\nРезультат: *{final_score}/{len(QUIZZES)}*"
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")]])

        await query.edit_message_text(result_text, parse_mode="Markdown", reply_markup=keyboard)

    elif data == "quiz_next":
        await send_quiz_message(query, context)

    elif data == "menu_puzzles":
        context.user_data["puzzle_index"] = 0
        await send_puzzle_edit(query, context)

    elif data.startswith("puzzle_ans_"):
        chosen = int(data.split("_")[2])
        p_index = context.user_data.get("puzzle_index", 0)
        puzzle = PUZZLES[p_index]
        correct = puzzle["answer"]

        if chosen == correct:
            result_text = f"✅ *Правильно!*\n\n{puzzle['explanation']}"
        else:
            result_text = f"❌ *Неверно.*\nПравильный ответ: «{puzzle['options'][correct]}»"

        next_index = p_index + 1
        context.user_data["puzzle_index"] = next_index

        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")]])
        try:
            await query.edit_message_caption(caption=result_text, parse_mode="Markdown", reply_markup=keyboard)
        except Exception:
            await query.message.reply_text(result_text, reply_markup=keyboard)
        context.user_data["last_is_photo"] = True

    elif data == "menu_rules":
        await query.edit_message_text("📜 *Правила:* цель — мат королю. Главная фишка — сброс фигур противника.", parse_mode="Markdown",
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="menu_main")]]))

    elif data == "menu_about":
        await query.edit_message_text("ℹ️ Сёги — традиционные японские шахматы с глубокой тактикой сбросов.", parse_mode="Markdown",
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="menu_main")]]))

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
async def send_quiz_message(query, context):
    q_index = context.user_data.get("quiz_index", 0)
    quiz = QUIZZES[q_index]
    text = f"🧠 *Вопрос {q_index + 1}/{len(QUIZZES)}*\n\n{quiz['question']}"
    keyboard = [[InlineKeyboardButton(opt, callback_data=f"quiz_ans_{i}")] for i, opt in enumerate(quiz["options"])]
    keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")])
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def send_puzzle_edit(query, context):
    p_index = context.user_data.get("puzzle_index", 0)
    puzzle = PUZZLES[p_index]
    board_img = draw_shogi_board(puzzle["board"], puzzle["cols"], puzzle["rows"], title=puzzle["title"])
    keyboard = [[InlineKeyboardButton(opt, callback_data=f"puzzle_ans_{i}")] for i, opt in enumerate(puzzle["options"])]
    keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")])
    
    try:
        await query.message.delete()
    except Exception:
        pass
    await query.message.chat.send_photo(photo=board_img, caption=puzzle["description"], reply_markup=InlineKeyboardMarkup(keyboard))

async def send_puzzle_new_message(message, context):
    p_index = context.user_data.get("puzzle_index", 0)
    puzzle = PUZZLES[p_index]
    board_img = draw_shogi_board(puzzle["board"], puzzle["cols"], puzzle["rows"], title=puzzle["title"])
    keyboard = [[InlineKeyboardButton(opt, callback_data=f"puzzle_ans_{i}")] for i, opt in enumerate(puzzle["options"])]
    keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")])
    await message.reply_photo(photo=board_img, caption=puzzle["description"], reply_markup=InlineKeyboardMarkup(keyboard))

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Используй /start для начала 🎌", reply_markup=main_menu_keyboard())

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
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("guide", guide_command))
    app.add_handler(CommandHandler("test", test_command))
    app.add_handler(CommandHandler("puzzle", puzzle_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown))
    print("🎌 Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
