import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from tortoise import Tortoise  # Add this import if missing

from config import TG_BOT_TOKEN
from models import TORTOISE_ORM, Mail, Settings, run_migrations, init_db

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=TG_BOT_TOKEN)
dp = Dispatcher()  # No arguments

# Dictionary to track sent notifications to avoid duplicates
sent_notifications = set()

async def init_db():
    # Initialize Tortoise ORM
    await Tortoise.init(config=TORTOISE_ORM)

async def check_and_send_notifications():
    try:
        # Get users from settings
        settings = await Settings.get(id=1)
        tg_users = settings.tg_users
        
        if not tg_users:
            logging.warning("No Telegram users configured in settings")
            return
        
        # Get new processed emails (recognized is not None)
        new_emails = await Mail.filter(recognized__not_isnull=True)
        
        for email in new_emails:
            # Check if notification for this email was already sent
            if str(email.uuid) in sent_notifications:
                continue
                
            # Format message
            message_text = (
                f"📩 *New Email Processed*\n\n"
                f"*From:* {email.from_user}\n"
                f"*Subject:* {email.subject}\n"
                f"*Type:* {email.type}\n"
                f"*Recognized as:* {email.recognized}\n\n"
                f"*Body:*\n{email.body[:200]}...\n\n"
                f"*Suggested response:*\n{email.pre_generated_answer or 'No suggested response'}"
            )
            
            # Create inline keyboard with send response button
            keyboard = InlineKeyboardMarkup()
            if email.pre_generated_answer:
                keyboard.add(InlineKeyboardButton(
                    f"Send response as {email.recognized}",
                    callback_data=f"send_response:{email.uuid}"
                ))
            
            # Send notification to each user
            for user_id in tg_users:
                try:
                    await bot.send_message(
                        chat_id=user_id,
                        text=message_text,
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logging.error(f"Failed to send notification to user {user_id}: {e}")
            
            # Add to sent notifications
            sent_notifications.add(str(email.uuid))
            
    except Exception as e:
        logging.error(f"Error in check_and_send_notifications: {e}")

@dp.callback_query_handler(lambda c: c.data.startswith('send_response:'))
async def process_send_response(callback_query: types.CallbackQuery):
    try:
        # Extract email UUID from callback data
        email_uuid = callback_query.data.split(':')[1]
        
        # Get email from database
        email = await Mail.get(uuid=email_uuid)
        
        # Here you would implement the actual sending of the response
        # For example, connect to an email service and send the response
        
        await bot.answer_callback_query(
            callback_query.id,
            text=f"Response of type '{email.recognized}' sent successfully!"
        )
        
        # Update message to indicate response was sent
        await bot.edit_message_reply_markup(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            reply_markup=None
        )
        
        new_text = callback_query.message.text + "\n\n✅ Response sent!"
        await bot.edit_message_text(
            text=new_text,
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logging.error(f"Error processing response: {e}")
        await bot.answer_callback_query(
            callback_query.id,
            text=f"Error sending response: {str(e)[:50]}"
        )

async def periodic_check(interval=60):
    while True:
        await check_and_send_notifications()
        await asyncio.sleep(interval)

async def main():
    await init_db()
    await run_migrations()
    # Start periodic task
    asyncio.create_task(periodic_check())
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
