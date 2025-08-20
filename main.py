from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

# Стани розмови
CHOOSING, CHOOSING_CATEGORY, TYPING_AMOUNT = range(3)

# Клавіатура головного меню
keyboard = [
    ["➕ Дохід", "➖ Витрата"],
    ["📊 Баланс"]
]
markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Категорії доходів і витрат з кнопкою "Назад"
income_categories = ["💼 Зарплата", "🎁 Подарунок", "🏦 Інше", "⬅️ Назад"]
expense_categories = ["🥗 Їжа", "🏠 Оренда", "🚌 Транспорт", "🎮 Розваги", "📦 Інше", "⬅️ Назад"]

# Сховище даних користувача
user_state = {}

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привіт! Обери дію з меню ⬇️",
        reply_markup=markup
    )
    return CHOOSING

# Обробка вибору дії
async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    if text == "➕ Дохід":
        user_state[user_id] = {"type": "income"}
        reply_markup = ReplyKeyboardMarkup(
            [[c] for c in income_categories],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await update.message.reply_text("Оберіть категорію доходу:", reply_markup=reply_markup)
        return CHOOSING_CATEGORY

    elif text == "➖ Витрата":
        user_state[user_id] = {"type": "expense"}
        reply_markup = ReplyKeyboardMarkup(
            [[c] for c in expense_categories],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await update.message.reply_text("Оберіть категорію витрати:", reply_markup=reply_markup)
        return CHOOSING_CATEGORY

    elif text == "📊 Баланс":
        balance = context.bot_data.get("balance", 0)
        await update.message.reply_text(f"Поточний баланс: {balance} грн")
        return CHOOSING

    else:
        await update.message.reply_text("Будь ласка, обери дію з меню.")
        return CHOOSING

# Обробка вибору категорії
async def handle_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    category = update.message.text
    user_id = update.effective_user.id

    if category == "⬅️ Назад":
        await update.message.reply_text("Повертаємось до головного меню ⬇️", reply_markup=markup)
        return CHOOSING

    user_data = user_state.get(user_id, {})
    user_data["category"] = category
    user_state[user_id] = user_data

    await update.message.reply_text("Введіть суму (наприклад: 150):", reply_markup=ReplyKeyboardRemove())
    return TYPING_AMOUNT

# Обробка введення суми
async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        amount = float(update.message.text)
    except ValueError:
        await update.message.reply_text("Введіть правильну суму, наприклад 150")
        return TYPING_AMOUNT

    data = user_state.get(user_id)
    tx_type = data.get("type")
    category = data.get("category")
    balance = context.bot_data.get("balance", 0)

    if tx_type == "income":
        balance += amount
        context.bot_data.setdefault("transactions", []).append({
            "тип": "дохід",
            "категорія": category,
            "сума": amount
        })
        await update.message.reply_text(f"✅ Дохід {amount} грн ({category}) додано.")

    elif tx_type == "expense":
        balance -= amount
        context.bot_data.setdefault("transactions", []).append({
            "тип": "витрата",
            "категорія": category,
            "сума": amount
        })
        await update.message.reply_text(f"💸 Витрата {amount} грн ({category}) додана.")

    context.bot_data["balance"] = balance
    await update.message.reply_text(f"Поточний баланс: {balance} грн", reply_markup=markup)
    return CHOOSING

# Обробка /cancel
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Скасовано.", reply_markup=markup)
    return CHOOSING

# Запуск бота
if __name__ == "__main__":
    app = ApplicationBuilder().token("TELEGRAM_TOKEN").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_choice)],
            CHOOSING_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_category)],
            TYPING_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()
