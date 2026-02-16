import logging
import asyncio
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from config import BOT_TOKEN
from handlers import (
    start, menu_button_handler,
    login_start, login_username, login_password,
    register_start, reg_username, reg_password, reg_firstname, reg_lastname, reg_phone, reg_region, reg_birthdate,
    plant_start, plant_bucket_id_handler, plant_location_handler, plant_photo_handler,
    logout_handler, cancel,
    show_products, show_cart, show_profile,
    add_to_cart_handler, checkout_handler,
    LOGIN_USERNAME, LOGIN_PASSWORD,
    REG_USERNAME, REG_PASSWORD, REG_FIRSTNAME, REG_LASTNAME, REG_PHONE, REG_REGION, REG_BIRTHDATE,
    PLANT_BUCKET_ID, PLANT_WAIT_LOC, PLANT_WAIT_PHOTO
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def login_callback_wrapper(update, context):
    """Wrapper to handle callback query for login start"""
    query = update.callback_query
    await query.answer()
    return await login_start(update, context)

async def register_callback_wrapper(update, context):
    query = update.callback_query
    await query.answer()
    return await register_start(update, context)

async def plant_callback_wrapper(update, context):
    query = update.callback_query
    await query.answer()
    return await plant_start(update, context)

def main():
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN is not set in .env file.")

    application = Application.builder().token(BOT_TOKEN).build()

    # -- Conversation Handlers --

    # Login
    login_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("login", login_start),
            CallbackQueryHandler(login_callback_wrapper, pattern="^login$")
        ],
        states={
            LOGIN_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_username)],
            LOGIN_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_password)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(login_conv_handler)

    # Register
    register_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("register", register_start),
            CallbackQueryHandler(register_callback_wrapper, pattern="^register$")
        ],
        states={
            REG_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_username)],
            REG_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_password)],
            REG_FIRSTNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_firstname)],
            REG_LASTNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_lastname)],
            REG_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_phone)],
            REG_REGION: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_region)],
            REG_BIRTHDATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_birthdate)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(register_conv_handler)

    # Worker Plant Tree
    plant_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("plant", plant_start),
            CallbackQueryHandler(plant_callback_wrapper, pattern="^plant_tree$")
        ],
        states={
            PLANT_BUCKET_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, plant_bucket_id_handler)],
            PLANT_WAIT_LOC: [MessageHandler(filters.LOCATION, plant_location_handler)],
            PLANT_WAIT_PHOTO: [MessageHandler(filters.PHOTO, plant_photo_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(plant_conv_handler)

    # -- Command Handlers --
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("products", show_products))
    application.add_handler(CommandHandler("cart", show_cart))
    application.add_handler(CommandHandler("me", show_profile))
    application.add_handler(CommandHandler("logout", logout_handler))

    # -- Callback Handlers --
    # Shop actions
    application.add_handler(CallbackQueryHandler(add_to_cart_handler, pattern="^add_"))
    application.add_handler(CallbackQueryHandler(checkout_handler, pattern="^checkout$"))
    
    # Generic Menu Actions
    application.add_handler(CallbackQueryHandler(menu_button_handler, pattern="^(products|cart|profile|tips|pricing|logout)$"))

    print("Bot is polling...")
    application.run_polling()

if __name__ == "__main__":
    main()
