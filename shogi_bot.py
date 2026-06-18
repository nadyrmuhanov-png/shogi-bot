import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, InputMediaPhoto
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
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
        "img_main": "hisha.jpg",
        "img_promoted": "hisha_promoted.jpg",
        "description": (
            "Hisha (飛車) — Ладья, одна из сильнейших фигур.\n\n"
            "♟ Ход: любое количество клеток по горизонтали или вертикали.\n"
            "⭐ После превращения: становится «Ryuo» (龍王) — Король-дракон. "
            "Добавляется ход на одну клетку по диагонали.\n\n"
            "💡 Стратегия: ладью лучше держать в центре или на открытых вертикалях."
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
            "⭐ После превращения: становится «Ryuma» (龍馬) — Конь-дракон. "
            "Добавляется ход на одну клетку по горизонтали/вертикали.\n\n"
            "💡 Слон контролирует длинные диагонали и опасен в миттельшпиле."
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
        "img_main": "gin.jpg",
        "img_promoted": "gin_promoted.jpg",
        "description": (
            "Ginsho (銀将) — Серебряный генерал.\n\n"
            "♟ Ход: одна клетка — вперёд, или по диагонали в любую сторону (5 направлений).\n"
            "⭐ После превращения: ходит как Золотой генерал.\n\n"
            "💡 Серебряный генерал гибок в атаке. Часто продвигается вперёд "
            "для поддержки наступления."
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
            "♟ Ход: прыжок — на две клетки вперёд и одну в сторону "
            "(только вперёд! в отличие от шахматного коня).\n"
            "⭐ После превращения: ходит как Золотой генерал.\n\n"
            "⚠️ Конь не может ходить с последних двух рядов — "
            "там его необходимо превратить."
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
            "♟ Ход: любое количество клеток только вперёд (как ладья, но только вперёд).\n"
            "⭐ После превращения: ходит как Золотой генерал.\n\n"
            "💡 Копьеносец стоит в углах доски в начале игры. "
            "Хорош для давления на вертикалях."
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
            "⭐ После превращения: становится «Tokin» (と金) — ходит как Золотой генерал.\n\n"
            "⚠️ Нельзя ставить две пешки на одной вертикали.\n"
            "⚠️ Нельзя ставить пешку с немедленным матом («утифу»).\n\n"
            "💡 Пешек 9 штук — больше всего. Превращённая пешка «Tokin» "
            "очень сильна и опасна для короля."
        ),
    },
}

# ==================== ВСЕ 8 ТЕСТОВ ====================
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
        "question": "What happens to captured pieces in shogi?",
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

# ==================== ЗАДАЧИ НА ХОД ====================
# ==================== ВСЕ 8 ЗАДАЧ НА ХОД ====================
PUZZLES = [
    {
        "title": "Задача 1: Запрещённый мат",
        "description": (
            "Король чёрных стоит на 1a. Пешка белых стоит на 1b.\n\n"
            "❓ Что произойдёт если пешка СБРОСОМ из руки встанет на 1b (вместо короля)?"
        ),
        "image": "t1.jpg",
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
        "image": "t2.jpg",
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
        "image": "t3.jpg",
        "options": [
            "Пешка остаётся пешкой",
            "Пешка обязана превратиться в Tokin",
            "Пешка убирается с доски",
            "Ничего не происходит"
        ],
        "answer": 1,
        "explanation": "Фигура обязана превратиться, если у неё больше нет возможности сделать ход (для пешки это 1-й ряд)."
    },
    {
        "title": "Задача 4: Двойной удар (Вилка)",
        "description": (
            "У вас в руке есть Слон (Kakugyo). На доске Король противника стоит на поле 7a, а Ладья — на 9c.\n\n"
            "❓ На какое поле нужно сбросить Слона, чтобы объявить вилку?"
        ),
        "image": "t4.jpg",
        "options": [
            "Сбросить Слона на 8b",
            "Сбросить Слона на 7c",
            "Сбросить Слона на 9a",
            "Сбросить Слона на 6b"
        ],
        "answer": 0,
        "explanation": "Правильно! Сброс Слона на поле 8b создает линейную угрозу (шах королю на 7a и одновременное нападение на ладью на 9c)."
    },
    {
        "title": "Задача 5: Цуме-сёги (Мат в 1 ход)",
        "description": (
            "Король соперника зажат в углу на 1a. Поля 1b и 2a атакованы вашими фигурами.\n"
            "У вас в руке остался Золотой генерал (Kinsho).\n\n"
            "❓ Куда сбросить Золото для немедленного мата?"
        ),
        "image": "t5.jpg",
        "options": [
            "Сбросить на 1b прямо перед Королем",
            "Сбросить на 2b",
            "Сбросить на 2a",
            "Ходов нет, это ничья"
        ],
        "answer": 0,
        "explanation": "Золотой генерал, сброшенный на 1b «в голову королю», объявляет мат, так как бьет все поля вокруг себя и защищен вашими тыловыми фигурами."
    },
    {
        "title": "Задача 6: Контратака в миттельшпиле",
        "description": (
            "Позиция на картинке: соперник обострил игру в центре. "
            "Ваш Король находится на 3f, но сейчас ВАШ ход.\n"
            "Взгляните на лагерь белых: их Король на 7b защищен только Ладьей на 8b.\n\n"
            "❓ У вас в руке есть Слон, Золото, Конь и Копье. Каким сокрушительным сбросом "
            "из руки можно сразу разрушить оборону противника и объявить вилку на Короля и Ладью?"
        ),
        "image": "t6.jpg",  # Сохрани скриншот {EB608DB6-64E3-4A0F-B05B-CCCB74BD1619}.png как t6.jpg
        "options": [
            "Сбросить Золото на 6b",
            "Сбросить Слона (Kakugyo) на 4e",
            "Сбросить Слона (Kakugyo) на 9c",
            "Сбросить Коня на 6d"
        ],
        "answer": 1,
        "explanation": (
            "Великолепно! Сброс Слона (Kakugyo) на поле 4e — это победный ход. "
            "Отсюда Слон по длинной диагонали объявляет шах Королю на 7b и одновременно "
            "атакует незащищенную Ладью на 2e. Белым придется тратить ход на защиту Короля, "
            "и вы заберете Ладью, перехватывая полную инициативу в партии!"
        )
    },
    {
        "title": "Задача 7: Матовая атака (Цуме в 2 хода)",
        "description": (
            "Позиция на картинке: игра перешла в решающую стадию эндшпиля. "
            "Вражеский Король находится на 8b, а ваше Золото на 7d контролирует важные поля.\n"
            "В руке у вас  выбор: Золото  и две пешки.\n\n"
            "❓ Вы начинаете матовую атаку и первым ходом сбрасываете Золото на поле 8c, объявляя шах. "
            "Король соперника вынужден бежать в угол на поле 7a. Каким вторым ходом вы ставите неизбежный мат?"
        ),
        "image": "t7.jpg",  # Сохрани скриншот {ECA4A5B6-5A5C-4057-819A-BA71733E2799}.png как t7.jpg
        "options": [
            "Продвинуть пешку на 9b",
            "Продвинуть Золотого генерала на поле 7b",
            "Сбросить Серебряного генерала на поле 8a",
            "Сбросить пешку на поле 8b"
        ],
        "answer": 1,
        "explanation": (
            "Абсолютно верно! После отступления Короля в угол на 7a, продвигая Золотого генерала на поле 7b ставит сокрушительный мат."
        )
    },
   {
        "title": "Задача 8: Финальный аккорд (Мат в 1 ход)",
        "description": (
            "Позиция на картинке: финальный штурм! Вражеский Король зажат на поле 2c.\n"
            "Ваша Ладья на 4b полностью контролирует 2-ю горизонталь, отрезая пути отхода.\n"
            "В руке у вас огромный выбор захваченных фигур (включая 4 Золотых генерала).\n\n"
            "❓ Найдите поле для сброса Золотого генерала (Kinsho), чтобы поставить мгновенный мат в 1 ход."
        ),
        "image": "t8.jpg",  # Сохрани скриншот {2DBDD12D-635E-400A-8888-9DF363E62CF3}.png как t8.jpg
        "options": [
            "Сбросить Золото на 2b (прямо перед Королем)",
            "Сбросить Золото на 1b",
            "Сбросить Золото на 3b",
            "Сбросить Золото на 2d"
        ],
        "answer": 2,
        "explanation": (
            "Абсолютно верно! Сброс Золотого генерала на поле 3b ставит неизбежный мат. Это победа!"
        )
    },
]
# ==================== КЛАВИАТУРЫ ====================
def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 Изучить фигуры", callback_data="menu_pieces")],
        [InlineKeyboardButton("🧠 Пройти тест", callback_data="menu_quiz")],
        [InlineKeyboardButton("♟ Задачи на ход", callback_data="menu_puzzles")],
        [InlineKeyboardButton("📜 Правила игры", callback_data="menu_rules")],
        [InlineKeyboardButton("ℹ️ О сёги", callback_data="menu_about")]
    ])

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

# ==================== ТЕКСТЫ ДЛЯ МЕНЮ ====================
START_TEXT = (
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

RULES_TEXT = (
    "📜 *Основные правила Сёги*\n\n"
    "🎯 *Цель:* поставить мат Королю противника.\n\n"
    "🗺 *Доска:* 9×9 клеток. Каждый игрок начинает с 20 фигурами.\n\n"
    "🔄 *Зона превращения:* три последних ряда противника.\n"
    "Большинство фигур могут превратиться, достигнув этой зоны.\n\n"
    "♻️ *Сброс (главная особенность!):*\n"
    "Захваченные фигуры переходят к тебе.\n"
    "Ты можешь в свой ход поставить захваченную фигуру "
    "на любую свободную клетку доски вместо обычного хода.\n\n"
    "⛔ *Запреты при сбросе:*\n"
    "• Нельзя ставить пешку на вертикаль, где уже есть своя пешка\n"
    "• Нельзя ставить пешку с немедленным матом (утифу)\n"
    "• Нельзя ставить фигуру туда, где у неё нет ходов\n\n"
    "🏳️ *Ничья:* возможна при повторении позиции 4 раза."
)

# ==================== КОМАНДЫ ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    if os.path.exists("doska.jpg"):
        with open("doska.jpg", "rb") as photo:
            await update.message.reply_photo(photo=photo, caption=START_TEXT, parse_mode="Markdown", reply_markup=main_menu_keyboard())
        context.user_data["last_is_photo"] = True
    else:
        await update.message.reply_text(START_TEXT, parse_mode="Markdown", reply_markup=main_menu_keyboard())
        context.user_data["last_is_photo"] = False

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
    await update.message.reply_text("📖 *Изучение фигур*\n\nВыбери фигуру:", parse_mode="Markdown", reply_markup=pieces_menu_keyboard())

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["quiz_index"] = 0
    context.user_data["quiz_score"] = 0
    await send_quiz_message(None, context, is_edit=False, update=update)

async def puzzle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["puzzle_index"] = 0
    await send_puzzle_message(None, context, is_edit=False, update=update)

# ==================== ОБРАБОТЧИК КНОПОК ====================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "menu_main":
        context.user_data.clear()
        try: await query.message.delete()
        except: pass
        
        if os.path.exists("doska.jpg"):
            with open("doska.jpg", "rb") as photo:
                await query.message.chat.send_photo(photo=photo, caption="🎌 *Главное меню*\n\nВыбери раздел:", parse_mode="Markdown", reply_markup=main_menu_keyboard())
            context.user_data["last_is_photo"] = True
        else:
            await query.message.chat.send_message("🎌 *Главное меню*\n\nВыбери раздел:", parse_mode="Markdown", reply_markup=main_menu_keyboard())
            context.user_data["last_is_photo"] = False

    elif data == "menu_pieces":
        is_photo = context.user_data.get("last_is_photo", False)
        context.user_data["last_is_photo"] = False
        if is_photo:
            try: await query.message.delete()
            except: pass
            await query.message.chat.send_message("📖 *Фигуры сёги*\n\nВыбери фигуру, чтобы узнать о ней подробнее:", parse_mode="Markdown", reply_markup=pieces_menu_keyboard())
        else:
            try: await query.edit_message_text("📖 *Фигуры сёги*\n\nВыбери фигуру, чтобы узнать о ней подробнее:", parse_mode="Markdown", reply_markup=pieces_menu_keyboard())
            except:
                try: await query.message.delete()
                except: pass
                await query.message.chat.send_message("📖 *Фигуры сёги*\n\nВыбери фигуру, чтобы узнать о ней подробнее:", parse_mode="Markdown", reply_markup=pieces_menu_keyboard())

    elif data.startswith("piece_"):
        key = data.replace("piece_", "")
        piece = PIECES.get(key)
        if piece:
            text = f"*{piece['emoji']} {piece['name']}*\n*Русское название: {piece['ru_name']}*\n\n{piece['description']}"
            media_group = []
            if os.path.exists(piece["img_main"]):
                media_group.append(InputMediaPhoto(open(piece["img_main"], "rb"), caption=text, parse_mode="Markdown"))
            if piece["img_promoted"] and os.path.exists(piece["img_promoted"]):
                media_group.append(InputMediaPhoto(open(piece["img_promoted"], "rb")))

            if media_group:
                try: await query.message.delete()
                except: pass
                await query.message.chat.send_media_group(media=media_group)
                await query.message.chat.send_message("🧭 Навигация:", reply_markup=back_to_main())
                context.user_data["last_is_photo"] = True
            else:
                try: await query.message.delete()
                except: pass
                await query.message.chat.send_message(f"⚠️ Фотографии для фигуры {piece['ru_name']} еще не загружены на server.\n\n{text}", parse_mode="Markdown", reply_markup=back_to_main())
                context.user_data["last_is_photo"] = False

    elif data == "menu_quiz":
        context.user_data["quiz_index"] = 0
        context.user_data["quiz_score"] = 0
        is_photo = context.user_data.get("last_is_photo", False)
        if is_photo:
            try: await query.message.delete()
            except: pass
            await send_quiz_message(query, context, is_edit=False, update=update)
        else:
            await send_quiz_message(query, context, is_edit=True)

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
            result_text = f"❌ *Неверно.*\nТы выбрал: «{quiz['options'][chosen]}»\nПравильный ответ: «{quiz['options'][correct]}»\n\n{quiz['explanation']}"

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
            if final_score == total: result_text += "\n🏆 Отлично! Ты знаешь сёги!"
            elif final_score >= total * 0.7: result_text += "\n👍 Хороший результат! Продолжай изучение."
            else: result_text += "\n📖 Рекомендую ещё раз изучить фигуры."
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Пройти ещё раз", callback_data="menu_quiz")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")]
            ])
        await query.edit_message_text(result_text, parse_mode="Markdown", reply_markup=keyboard)
        context.user_data["last_is_photo"] = False

    elif data == "quiz_next":
        await send_quiz_message(query, context, is_edit=True)

    elif data == "quiz_prev":
        context.user_data["quiz_index"] = max(0, context.user_data.get("quiz_index", 1) - 1)
        await send_quiz_message(query, context, is_edit=True)

    elif data == "menu_puzzles":
        context.user_data["puzzle_index"] = 0
        try: await query.message.delete()
        except: pass
        await send_puzzle_message(query, context, is_edit=False, update=update)

    elif data.startswith("puzzle_ans_"):
        chosen = int(data.split("_")[2])
        p_index = context.user_data.get("puzzle_index", 0)
        puzzle = PUZZLES[p_index]
        correct = puzzle["answer"]

        if chosen == correct:
            result_text = f"✅ *Правильно!*\n\n{puzzle['explanation']}"
        else:
            result_text = f"❌ *Неверно.*\nПравильный ответ: «{puzzle['options'][correct]}»\n\n{puzzle['explanation']}"

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

        try: await query.edit_message_caption(caption=result_text, parse_mode="Markdown", reply_markup=keyboard)
        except: await query.message.reply_text(result_text, parse_mode="Markdown", reply_markup=keyboard)
        context.user_data["last_is_photo"] = True

    elif data == "puzzle_next":
        try: await query.message.delete()
        except: pass
        await send_puzzle_message(query, context, is_edit=False, update=update)

    elif data == "puzzle_prev":
        context.user_data["puzzle_index"] = max(0, context.user_data.get("puzzle_index", 1) - 1)
        try: await query.message.delete()
        except: pass
        await send_puzzle_message(query, context, is_edit=False, update=update)

    elif data == "menu_rules":
        try: await query.message.delete()
        except: pass
        
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")]])
        if os.path.exists("doska.jpg"):
            with open("doska.jpg", "rb") as photo:
                await query.message.chat.send_photo(photo=photo, caption=RULES_TEXT, parse_mode="Markdown", reply_markup=markup)
            context.user_data["last_is_photo"] = True
        else:
            await query.message.chat.send_message(RULES_TEXT, parse_mode="Markdown", reply_markup=markup)
            context.user_data["last_is_photo"] = False

    elif data == "menu_about":
        is_photo = context.user_data.get("last_is_photo", False)
        context.user_data["last_is_photo"] = False
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
            "С 2013 года компьютерные программы стабильно превосходят профессиональных игроков.\n\n"
            "🎌 *Уникальность:*\n"
            "Главное отличие от шахмат — сброс захваченных фигур.\n"
            "Это делает партии более динамичными и сложными."
        )
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="menu_main")]])
        if is_photo:
            try: await query.message.delete()
            except: pass
            await query.message.chat.send_message(about_text, parse_mode="Markdown", reply_markup=markup)
        else:
            try: await query.edit_message_text(about_text, parse_mode="Markdown", reply_markup=markup)
            except:
                try: await query.message.delete()
                except: pass
                await query.message.chat.send_message(about_text, parse_mode="Markdown", reply_markup=markup)

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
async def send_quiz_message(query, context, is_edit=True, update=None):
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
    
    if is_edit and query:
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        target = query.message.chat if query else update.message.chat
        await target.send_message(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    context.user_data["last_is_photo"] = False

async def send_puzzle_message(query, context, is_edit=True, update=None):
    p_index = context.user_data.get("puzzle_index", 0)
    puzzle = PUZZLES[p_index]
    total = len(PUZZLES)
    text = f"♟ *Задача {p_index + 1}/{total}: {puzzle['title']}*\n\n{puzzle['description']}"
    
    keyboard = []
    for i, option in enumerate(puzzle["options"]):
        keyboard.append([InlineKeyboardButton(option, callback_data=f"puzzle_ans_{i}")])
    
    nav_row = []
    if p_index > 0:
        nav_row.append(InlineKeyboardButton("◀️ Назад", callback_data="puzzle_prev"))
    nav_row.append(InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main"))
    keyboard.append(nav_row)
    markup = InlineKeyboardMarkup(keyboard)

    target_chat = query.message.chat if query else update.message.chat

    if os.path.exists(puzzle["image"]):
        await target_chat.send_photo(photo=open(puzzle["image"], "rb"), caption=text, parse_mode="Markdown", reply_markup=markup)
    else:
        await target_chat.send_message(f"⚠️ Ошибка: файл {puzzle['image']} не найден.\n\n{text}", parse_mode="Markdown", reply_markup=markup)
    context.user_data["last_is_photo"] = True

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Используй /start для начала или выбери раздел 🎌", reply_markup=main_menu_keyboard())

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
