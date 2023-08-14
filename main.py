import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
from telegram import Update
from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram import KeyboardButton, ReplyKeyboardMarkup, Update, Bot 
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackContext,
    filters as Filters,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    Updater,
    ContextTypes,
    ConversationHandler,
)

#### Logger
import logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# State constants for conversation
MAIN_MENU, CANCEL, REGISTER, REGISTER_1, UNREGISTER, BOOK_SLOT, REBOOK_BOOL, ACCEPT_SLOT, HOST_SLOT,  DROP_SLOT  = range(10)

# this should be in a db
MEMBERS = [
    '10',
    '11',
    '12',
    '13',
    '14'
]

REGISTERED_MEMBERS = {}
REGISTERED_USERS = {}
BOOKED = {}
LIVE_SLOTS = ["5-10", "2-3"]
OFFER_SLOTS = [ [ "Cancel"]]


# this should also be in a db
ADMINS = [
    'kawa_gucci'
]

################################## MARKUP
yesno_keyboard=  [[ "YES", "NO"]]

kb1 = ReplyKeyboardMarkup(yesno_keyboard, resize_keyboard=True, one_time_keyboard=True)

################################## STATE UPDATES
async def main_menu(update, context):
    await update.message.reply_text("Main menu:\n\n"
                              "1. /Register\n\n"
                              "2. /Unregister\n\n"
                              "3. /Book\n\n"
                              "4. /Host")

    return MAIN_MENU 

async def member_register_1(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    registration_number = update.message.text

    # You can store the registration number in a database or in-memory structure here
    # For now, we'll just print it
    if registration_number not in MEMBERS:
        await update.message.reply_text("Your roll number is not eligible")
        return MAIN_MENU
    
    if registration_number in REGISTERED_MEMBERS: 
        if REGISTERED_MEMBERS[registration_number] == user_id:
            await update.message.reply_text("Your telegram account is alread linked to this roll_no")
        else:
            await update.message.reply_text("This roll_no is linked to another telegram account")
    else:
        REGISTERED_MEMBERS[registration_number] = user_id
        REGISTERED_USERS[user_id] = registration_number

        await update.message.reply_text("Your telegram account is linked to this roll_no from now")

    print(f"User {user_id} registered with registration number: {registration_number}")
    return MAIN_MENU

async def member_register(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Please enter your roll number")
    return REGISTER_1

async def member_deregister(update:Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id

    if user_id in REGISTERED_USERS:
        val = REGISTERED_USERS[user_id]
        REGISTERED_USERS.pop(user_id)
        REGISTERED_MEMBERS.pop(val)
    else:
        await update.message.reply_text("You are not registered")
    return MAIN_MENU

async def book(update:Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id

    if user_id not in REGISTERED_USERS:
        await update.message.reply_text("You have not registered. Please /Register to book")
        return MAIN_MENU

    if user_id in BOOKED:
        await update.message.reply_text("Your slot has been already booked. Do you want to rebook?",reply_markup=kb1)
        return REBOOK_BOOL 

    ls = OFFER_SLOTS
    ls.append(LIVE_SLOTS)
    live_kb = ReplyKeyboardMarkup(ls, input_field_placeholder="Please select a slot" ,resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        "Please select slot",
        reply_markup=live_kb,
    )
    return ACCEPT_SLOT 

async def rebook(update:Update, context: CallbackContext) -> int:
    user = update.message.text
    print(user)

    if user == "NO":
        return MAIN_MENU

    ls = OFFER_SLOTS
    ls.append(LIVE_SLOTS)
    live_kb = ReplyKeyboardMarkup(ls, input_field_placeholder="Please select a slot" ,resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        "Please select slot",
        reply_markup=live_kb,
    )
    
    return ACCEPT_SLOT


async def accept_slot(update: Update, context:CallbackContext )-> int:

    print(update.message.text)
    if update.message.text == "Cancel" :
        return MAIN_MENU
    
    if update.message.text not in LIVE_SLOTS:
        await update.message.reply_text("This slot is invalid.")
        return MAIN_MENU


    BOOKED[update.message.from_user.id] = update.message.text

    await update.message.reply_text("Your slot has been booked!")
    return MAIN_MENU

async def drop(update: Update, context:CallbackContext )-> int:
    return 4


# Function to cancel the conversation
def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Operation Cancelled.")
    return ConversationHandler.END

def main():
    # Replace 'YOUR_BOT_TOKEN' with your actual bot token
    application = ApplicationBuilder().token(BOT_TOKEN).build()


    # Create a ConversationHandler with two states
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('Start', main_menu)],
        states={
            MAIN_MENU:[CommandHandler('Register', member_register), CommandHandler('Unregister', member_deregister), CommandHandler('Book', book), CommandHandler('Host', host)],
            REGISTER_1: [MessageHandler(Filters.TEXT & ~Filters.COMMAND, member_register_1)],
            REBOOK_BOOL: [MessageHandler(Filters.TEXT & ~Filters.COMMAND, rebook)],
            ACCEPT_SLOT: [MessageHandler(Filters.TEXT & ~Filters.COMMAND, accept_slot)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
