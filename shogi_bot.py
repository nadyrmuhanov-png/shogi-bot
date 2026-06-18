import logging
import os
import random
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

# ==================== ТЕСТ 1: УГАДАЙ ПО ФОТО ====================
MEMORY_TEST_BY_PHOTO = [
    {
        "image": "gyoku.jpg",
        "question": "🖼 Какая фигура изображена на фотографии?",
        "options": ["Король (Osho/Gyoku)", "Золотой генерал (Kinsho)", "Серебряный генерал (Ginsho)", "Пешка (Fuhyo)"],
        "answer": 0,
        "explanation": "Это Король — главная фигура на доске. Задача всей партии — защитить своего и поймать чужого Короля."
    },
    {
        "image": "hisha.jpg",
        "question": "🖼 Какая фигура изображена на фотографии?",
        "options": ["Слон (Kakugyo)", "Ладья (Hisha)", "Копьеносец (Kyosha)", "Конь (Keima)"],
        "answer": 1,
        "explanation": "Это Ладья (Hisha). Её иероглиф переводится как «летающая колесница»."
    },
    {
        "image": "kaku.jpg",
        "question": "🖼 Какая фигура изображена на фотографии?",
        "options": ["Пешка (Fuhyo)", "Золотой генерал (Kinsho)", "Слон (Kakugyo)", "Король"],
        "answer": 2,
        "explanation": "Это Слон (Kakugyo). Его иероглиф переводится как «угловой ходок»."
    },
    {
        "image": "kin.jpg",
        "question": "🖼 Какая фигура изображена на фотографии?",
        "options": ["Серебряный генерал (Ginsho)", "Золотой генерал (Kinsho)", "Копьеносец (Kyosha)", "Конь (Keima)"],
        "answer": 1,
        "explanation": "Это Золотой генерал (Kinsho). Иероглиф 金 (золото) — основа большинства защитных крепостей."
    },
    {
        "image": "gin.jpg",
        "question": "🖼 Какая фигура изображена на фотографии?",
        "options": ["Серебряный генерал (Ginsho)", "Золотой генерал (Kinsho)", "Пешка (Fuhyo)", "Король"],
        "answer": 0,
        "explanation": "Это Серебряный генерал (Ginsho). Иероглиф 銀 (серебро) снизу имеет характерные четыре черты."
    },
    {
        "image": "kei.jpg",
        "question": "🖼 Какая фигура изображена на фотографии?",
        "options": ["Копьеносец (Kyosha)", "Пешка (Fuhyo)", "Ладья (Hisha)", "Конь (Keima)"],
        "answer": 3,
        "explanation": "Это Конь (Keima). На иероглифе сверху есть элемент, напоминающий крышу или рожки."
    },
    {
        "image": "kyo.jpg",
        "question": "🖼 Какая фигура изображена на фотографии?",
        "options": ["Копьеносец (Kyosha)", "Пешка (Fuhyo)", "Слон (Kakugyo)", "Золотой генерал (Kinsho)"],
        "answer": 0,
        "explanation": "Это Копьеносец (Kyosha). Первый иероглиф 香 означает «ароматный» или «благовоние»."
    },
    {
        "image": "fu.jpg",
        "question": "🖼 Какая фигура изображена на фотографии?",
        "options": ["Конь (Keima)", "Пешка (Fuhyo)", "Серебряный генерал (Ginsho)", "Король"],
        "answer": 1,
        "explanation": "Это Пешка (Fuhyo). Самый простой иероглиф 歩, означающий «пеший шаг»."
    },
]

# ==================== ТЕСТ 2: НАЙДИ ПО ТЕКСТУ ====================
MEMORY_TEST_BY_TEXT = [
    {
        "question": "📝 Как выглядит Король (Osho/Gyoku)? Посмотрите на медиагруппу выше и выберите букву:",
        "images": ["gyoku.jpg", "kin.jpg", "gin.jpg", "fu.jpg"],
        "correct_letter": "A",
        "explanation": "Верно! Король — самый крупный пятиугольник, часто имеет точку в нижнем иероглифе у младшего игрока."
    },
    {
        "question": "📝 Как выглядит Ладья (Hisha)? Посмотрите на медиагруппу выше и выберите букву:",
        "images": ["kaku.jpg", "hisha.jpg", "kyo.jpg", "kei.jpg"],
        "correct_letter": "B",
        "explanation": "Верно! Ладья (Hisha) выделяется сложным верхним иероглифом «飛» (летать)."
    },
    {
        "question": "📝 Как выглядит Конь (Keima)? Посмотрите на медиагруппу выше и выберите букву:",
        "images": ["fu.jpg", "gin.jpg", "kei.jpg", "kin.jpg"],
        "correct_letter": "C",
        "explanation": "Верно! Иероглиф Коня (桂) содержит элемент дерева слева."
    },
    {
        "question": "📝 Как выглядит Пешка (Fuhyo)? Посмотрите на медиагруппу выше и выберите букву:",
        "images": ["kyo.jpg", "kin.jpg", "gyoku.jpg", "fu.jpg"],
        "correct_letter": "D",
        "explanation": "Верно! Пешка обозначается иероглифом 歩 (шаг)."
    },
]

# ==================== ТЕСТ 3: ОБЩАЯ ТЕОРИЯ ====================
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

# ==================== ЗАДАЧИ НА ХОД ====================
PUZZLES = [
    {
        "title": "Задача 1: Запрещённый мат",
        "description": (
            "Король чёрных стоит на 1a. Пешка белых стоит на 1b.\n\n"
            "❓ Что произойдёт если пешка СБРОСОМ из руки встанет на 1b?"
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
        "explanation": "Правильно! Сброс Слона на поле 8b создает угрозу Королю на 7a и одновременное нападение на ладью на 9c."
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
            "Сбросить на 1b прямо перед Королём",
            "Сбросить на 2b",
            "Сбросить на 2a",
            "Ходов нет, это ничья"
        ],
        "answer": 0,
        "explanation": "Золотой генерал, сброшенный на 1b «в голову королю», объявляет мат, так как бьет все поля вокруг себя."
    },
    {
        "title": "Задача 6: Контратака в миттельшпиле",
        "description": (
            "Король противника на 7b защищен только Ладьей на 8b.\n"
            "У вас в руке есть Слон, Золото, Конь и Копьё.\n\n"
            "❓ Каким сбросом из руки можно сразу создать вилку на Короля и Ладью?"
        ),
        "image": "t6.jpg",
        "options": [
            "Сбросить Золото на 6b",
            "Сбросить Слона (Kakugyo) на 4e",
            "Сбросить Слона (Kakugyo) на 9c",
            "Сбросить Коня на 6d"
        ],
        "answer": 1,
        "explanation": "Сброс Слона на поле 4e — победный ход. Отсюда Слон по длинной диагонали объявляет шах Королю на 7b и атакует Ладью на 2e."
    },
    {
        "title": "Задача 7: Матовая атака (Цуме в 2 хода)",
        "description": (
            "Вражеский Король на 8b. В руке у вас Золото и две пешки.\n\n"
            "❓ Первым ходом вы сбрасываете Золото на 8c (шах). Король бежит на 7a. "
            "Каким вторым ходом вы ставите мат?"
        ),
        "image": "t7.jpg",
        "options": [
            "Продвинуть пешку на 9b",
            "Продвинуть Золотого генерала на поле 7b",
            "Сбросить Серебряного генерала на поле 8a",
            "Сбросить пешку на поле 8b"
        ],
        "answer": 1,
        "explanation": "После отступления Короля в угол на 7a, продвигая Золотого генерала на поле 7b ставит сокрушительный мат."
    },
    {
        "title": "Задача 8: Финальный аккорд (Мат в 1 ход)",
        "description": (
            "Вражеский Король зажат на поле 2c. Ваша Ладья на 4b контролирует 2-ю горизонталь.\n"
            "В руке много фигур включая Золотых генералов.\n\n"
            "❓ Куда сбросить Золотого генерала (Kinsho) для мгновенного мата?"
        ),
        "image": "t8.jpg",
        "options": [
            "Сбросить Золото на 2b (прямо перед Королём)",
            "Сбросить Золото на 1b",
            "Сбросить Золото на 3b",
            "Сбросить Золото на 2d"
        ],
        "answer": 2,
        "explanation": "Сброс Золотого генерала на поле 3b ставит неизбежный мат. Это победа!"
    },
]

# ==================== ТЕКСТЫ ====================
START_TEXT = (
    "🎌 *Добро пожаловать в обучающий бот по Сёги!*\n\n"
    "将棋 — японские шахматы, одна из древнейших стратегических игр мира.\n\n"
    "Здесь ты можешь:\n"
    "📖 Изучить все фигуры и их ходы\n"
    "🧠 Проверить визуальную память и знания\n"
    "♟ Решить задачи на лучший ход\n\n"
    "Выбери раздел или используй команды:\n"
    "/guide — обучение фигурам\n"
    "/test — пройти теоретический тест\n"
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

# ==================== КЛАВИАТУРЫ ====================
def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 Изучить фигуры", callback_data="menu_pieces")],
        [InlineKeyboardButton("🧠 Тест: Общая теория", callback_data="menu_quiz")],
        [InlineKeyboardButton("🖼 Тест: Угадай по фото", callback_data="menu_test_photo")],
        [InlineKeyboardButton("📝 Тест: Найди по тексту", callback_data="menu_test_text")],
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
        "/puzzle — Задачи на ход\n"
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

    # --- ГЛАВНОЕ МЕНЮ ---
    if data == "menu_main":
        context.user_data.clear()
        try:
            await query.message.delete()
        except:
            pass
        if os.path.exists("doska.jpg"):
            with open("doska.jpg", "rb") as photo:
                await query.message.chat.send_photo(photo=photo, caption="🔹 *Главное меню*\n\nВыбери раздел:", parse_mode="Markdown", reply_markup=main_menu_keyboard())
            context.user_data["last_is_photo"] = True
        else:
            await query.message.chat.send_message("🔹 *Главное меню*\n\nВыбери раздел:", parse_mode="Markdown", reply_markup=main_menu_keyboard())
            context.user_data["last_is_photo"] = False

    # --- СПИСОК ФИГУР ---
    elif data == "menu_pieces":
        is_photo = context.user_data.get("last_is_photo", False)
        context.user_data["last_is_photo"] = False
        if is_photo:
            try:
                await query.message.delete()
            except:
                pass
            await query.message.chat.send_message("📖 *Фигуры сёги*\n\nВыбери фигуру, чтобы узнать о ней подробнее:", parse_mode="Markdown", reply_markup=pieces_menu_keyboard())
        else:
            try:
                await query.edit_message_text("📖 *Фигуры сёги*\n\nВыбери фигуру, чтобы узнать о ней подробнее:", parse_mode="Markdown", reply_markup=pieces_menu_keyboard())
            except:
                try:
                    await query.message.delete()
                except:
                    pass
                await query.message.chat.send_message("📖 *Фигуры сёги*\n\nВыбери фигуру, чтобы узнать о ней подробнее:", parse_mode="Markdown", reply_markup=pieces_menu_keyboard())

    # --- КОНКРЕТНАЯ ФИГУРА ---
    elif data.startswith("piece_"):
        key = data.replace("piece_", "")
        piece = PIECES.get(key)
        if piece:
            text = f"*{piece['emoji']} {piece['name']}*\n*Русское название: {piece['ru_name']}*\n\n{piece['description']}"
            media_group = []
            if os.path.exists(piece["img_main"]):
                media_group.append(InputMediaPhoto(open(piece["img_main"], "rb"), caption=text, parse_mode="Markdown"))
            if piece["img_promoted"] and os.path.exists(piece["img_promoted"]):
                media_group.append(InputMediaPhoto(open(piece["img_promoted"], "rb"), caption="⭐ Превращённая форма"))
            if media_group:
                try:
                    await query.message.delete()
                except:
                    pass
                await query.message.chat.send_media_group(media=media_group)
                await query.message.chat.send_message("🧭 Навигация:", reply_markup=back_to_main())
                context.user_data["last_is_photo"] = True
            else:
                try:
                    await query.message.delete()
                except:
                    pass
                await query.message.chat.send_message(f"⚠️ Фото для фигуры {piece['ru_name']} ещё не загружены.\n\n{text}", parse_mode="Markdown", reply_markup=back_to_main())
                context.user_data["last_is_photo"] = False

    # --- ТЕСТ: ОБЩАЯ ТЕОРИЯ ---
    elif data == "menu_quiz":
        context.user_data["quiz_index"] = 0
        context.user_data["quiz_score"] = 0
        is_photo = context.user_data.get("last_is_photo", False)
        if is_photo:
            try:
                await query.message.delete()
            except:
                pass
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
            if final_score == total:
                result_text += "\n🏆 Отлично! Ты знаешь сёги!"
            elif final_score >= total * 0.7:
                result_text += "\n👍 Хороший результат!"
            else:
                result_text += "\n📖 Рекомендую ещё раз изучить фигуры."
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

    # --- ТЕСТ: УГАДАЙ ПО ФОТО ---
    elif data == "menu_test_photo":
        context.user_data["test_photo_index"] = 0
        context.user_data["test_photo_score"] = 0
        try:
            await query.message.delete()
        except:
            pass
        await send_test_photo_message(query, context, update=update)

    elif data.startswith("tp_ans_"):
        chosen = int(data.split("_")[2])
        index = context.user_data.get("test_photo_index", 0)
        item = MEMORY_TEST_BY_PHOTO[index]
        score = context.user_data.get("test_photo_score", 0)

        if chosen == item["answer"]:
            result_text = f"✅ *Верно!*\n\n{item['explanation']}"
            context.user_data["test_photo_score"] = score + 1
        else:
            result_text = f"❌ *Неверно.*\nПравильный ответ: «{item['options'][item['answer']]}»\n\n{item['explanation']}"

        next_index = index + 1
        context.user_data["test_photo_index"] = next_index

        if next_index < len(MEMORY_TEST_BY_PHOTO):
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"➡️ Следующая фигура ({next_index + 1}/{len(MEMORY_TEST_BY_PHOTO)})", callback_data="tp_next")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")]
            ])
        else:
            final_score = context.user_data.get("test_photo_score", 0)
            result_text += f"\n\n🏁 *Визуальный тест завершён!*\nВаш результат: *{final_score}/{len(MEMORY_TEST_BY_PHOTO)}*"
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Начать заново", callback_data="menu_test_photo")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")]
            ])
        try:
            await query.edit_message_caption(caption=result_text, parse_mode="Markdown", reply_markup=keyboard)
        except:
            await query.message.reply_text(result_text, parse_mode="Markdown", reply_markup=keyboard)

    elif data == "tp_next":
        try:
            await query.message.delete()
        except:
            pass
        await send_test_photo_message(query, context, update=update)

    # --- ТЕСТ: НАЙДИ ПО ТЕКСТУ ---
    elif data == "menu_test_text":
        context.user_data["test_text_index"] = 0
        context.user_data["test_text_score"] = 0
        try:
            await query.message.delete()
        except:
            pass
        await send_test_text_message(query, context, update=update)

    elif data.startswith("tt_ans_"):
        chosen_letter = data.split("_")[2]
        index = context.user_data.get("test_text_index", 0)
        item = MEMORY_TEST_BY_TEXT[index]
        score = context.user_data.get("test_text_score", 0)

        if chosen_letter == item["correct_letter"]:
            result_text = f"✅ *Великолепно!*\n\n{item['explanation']}"
            context.user_data["test_text_score"] = score + 1
        else:
            result_text = f"❌ *Ошибочка.*\nПравильный вариант под буквой: *{item['correct_letter']}*\n\n{item['explanation']}"

        next_index = index + 1
        context.user_data["test_text_index"] = next_index

        if next_index < len(MEMORY_TEST_BY_TEXT):
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"➡️ Следующий вопрос ({next_index + 1}/{len(MEMORY_TEST_BY_TEXT)})", callback_data="tt_next")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")]
            ])
        else:
            final_score = context.user_data.get("test_text_score", 0)
            result_text += f"\n\n🏁 *Тест на поиск фигур завершён!*\nВаш результат: *{final_score}/{len(MEMORY_TEST_BY_TEXT)}*"
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Начать заново", callback_data="menu_test_text")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")]
            ])
        try:
            await query.edit_message_caption(caption=result_text, parse_mode="Markdown", reply_markup=keyboard)
        except:
            await query.message.reply_text(result_text, parse_mode="Markdown", reply_markup=keyboard)

    elif data == "tt_next":
        try:
            await query.message.delete()
        except:
            pass
        await send_test_text_message(query, context, update=update)

    # --- ЗАДАЧИ НА ХОД ---
    elif data == "menu_puzzles":
        context.user_data["puzzle_index"] = 0
        try:
            await query.message.delete()
        except:
            pass
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
        try:
            await query.edit_message_caption(caption=result_text, parse_mode="Markdown", reply_markup=keyboard)
        except:
            await query.message.reply_text(result_text, parse_mode="Markdown", reply_markup=keyboard)
        context.user_data["last_is_photo"] = True

    elif data == "puzzle_next" or data == "puzzle_prev":
        if data == "puzzle_prev":
            context.user_data["puzzle_index"] = max(0, context.user_data.get("puzzle_index", 1) - 1)
        try:
            await query.message.delete()
        except:
            pass
        await send_puzzle_message(query, context, is_edit=False, update=update)

    # --- ПРАВИЛА ---
    elif data == "menu_rules":
        try:
            await query.message.delete()
        except:
            pass
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")]])
        if os.path.exists("doska.jpg"):
            with open("doska.jpg", "rb") as photo:
                await query.message.chat.send_photo(photo=photo, caption=RULES_TEXT, parse_mode="Markdown", reply_markup=markup)
            context.user_data["last_is_photo"] = True
        else:
            await query.message.chat.send_message(RULES_TEXT, parse_mode="Markdown", reply_markup=markup)
            context.user_data["last_is_photo"] = False

    # --- О СЁГИ ---
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
            "🎌 *Уникальность:*\n"
            "Главное отличие от шахмат — сброс захваченных фигур.\n"
            "Это делает партии более динамичными и сложными."
        )
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="menu_main")]])
        if is_photo:
            try:
                await query.message.delete()
            except:
                pass
            await query.message.chat.send_message(about_text, parse_mode="Markdown", reply_markup=markup)
        else:
            try:
                await query.edit_message_text(about_text, parse_mode="Markdown", reply_markup=markup)
            except:
                await query.message.chat.send_message(about_text, parse_mode="Markdown", reply_markup=markup)

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
async def send_test_photo_message(query, context, update=None):
    index = context.user_data.get("test_photo_index", 0)
    item = MEMORY_TEST_BY_PHOTO[index]
    total = len(MEMORY_TEST_BY_PHOTO)
    text = f"🖼 *Тест на память ({index + 1}/{total})*\n\n{item['question']}"
    keyboard = []
    for i, option in enumerate(item["options"]):
        keyboard.append([InlineKeyboardButton(option, callback_data=f"tp_ans_{i}")])
    keyboard.append([InlineKeyboardButton("🏠 Меню", callback_data="menu_main")])
    target_chat = query.message.chat if query else update.message.chat
    if os.path.exists(item["image"]):
        await target_chat.send_photo(photo=open(item["image"], "rb"), caption=text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await target_chat.send_message(f"⚠️ Файл {item['image']} не найден.\n\n{text}", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    context.user_data["last_is_photo"] = True

async def send_test_text_message(query, context, update=None):
    index = context.user_data.get("test_text_index", 0)
    item = MEMORY_TEST_BY_TEXT[index]
    total = len(MEMORY_TEST_BY_TEXT)
    target_chat = query.message.chat if query else update.message.chat
    letters = ["A", "B", "C", "D"]
    media_group = []
    for i, img_path in enumerate(item["images"]):
        if os.path.exists(img_path):
            media_group.append(InputMediaPhoto(open(img_path, "rb"), caption=f"Вариант {letters[i]}"))
    if media_group:
        await target_chat.send_media_group(media=media_group)
    text = f"📝 *Тест наоборот ({index + 1}/{total})*\n\n{item['question']}"
    keyboard = [
        [
            InlineKeyboardButton("Вариант A", callback_data="tt_ans_A"),
            InlineKeyboardButton("Вариант B", callback_data="tt_ans_B")
        ],
        [
            InlineKeyboardButton("Вариант C", callback_data="tt_ans_C"),
            InlineKeyboardButton("Вариант D", callback_data="tt_ans_D")
        ],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")]
    ]
    await target_chat.send_message(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    context.user_data["last_is_photo"] = False

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
        await target_chat.send_message(f"⚠️ Файл {puzzle['image']} не найден.\n\n{text}", parse_mode="Markdown", reply_markup=markup)
    context.user_data["last_is_photo"] = True

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Используй /start для начала или выбери раздел 🎌", reply_markup=main_menu_keyboard())

# ==================== ЗАПУСК ====================
async def post_init(application):
    await application.bot.set_my_commands([
        BotCommand("start", "Главное меню"),
        BotCommand("guide", "Изучение фигур"),
        BotCommand("test", "Пройти теоретический тест"),
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
    app.add_handler(MessageHandler(filters.COMMAND, unknown))
    print("🎌 Бот Сёги запущен! Нажми Ctrl+C для остановки.")
    app.run_polling()

if __name__ == "__main__":
    main()
