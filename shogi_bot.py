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

if name == "main":
    main()
