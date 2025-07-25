import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from tortoise import Tortoise
from datetime import datetime

from config import TG_BOT_TOKEN
from models import TORTOISE_ORM, Mail, Settings, run_migrations, init_db
from models.mail import MailNotification

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TG_BOT_TOKEN)
dp = Dispatcher()

async def init_db():
    await Tortoise.init(config=TORTOISE_ORM)

async def check_and_send_notifications():
    try:
        settings = await Settings.get(id=1)
        tg_users = settings.tg_users
        if not tg_users:
            logging.warning("No Telegram users configured in settings")
            return
        new_emails = await Mail.filter(recognized__not_isnull=True)
        if not new_emails:
            return
        email_uuids = [email.uuid for email in new_emails]
        notifications = await MailNotification.filter(mail_id__in=email_uuids).all()
        notified_set = set((n.mail_id, n.user_id) for n in notifications)
        for email in new_emails:
            for user_id in tg_users:
                if (email.uuid, user_id) in notified_set:
                    continue
                message_text = (
                    f"📩 *New Email Processed*\n\n"
                    f"*From:* {email.from_user}\n"
                    f"*Subject:* {email.subject}\n"
                    f"*Type:* {email.type}\n"
                    f"*Recognized as:* {email.recognized}\n\n"
                    f"*Body:*\n{email.body[:200]}...\n\n"
                    f"*Suggested response:*\n{email.pre_generated_answer or 'No suggested response'}"
                )
                builder = InlineKeyboardBuilder()
                if email.pre_generated_answer:
                    builder.button(
                        text=f"Send response as {email.recognized}",
                        callback_data=f"send_response:{email.uuid}"
                    )
                keyboard = builder.as_markup()
                try:
                    await bot.send_message(
                        chat_id=user_id,
                        text=message_text,
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
                    await MailNotification.create(mail=email, user_id=user_id, sent_at=datetime.utcnow())
                except Exception as e:
                    logging.error(f"Failed to send notification to user {user_id}: {e}")
    except Exception as e:
        logging.error(f"Error in check_and_send_notifications: {e}")

@dp.callback_query(F.data.startswith('send_response:'))
async def process_send_response(callback: types.CallbackQuery):
    try:
        email_uuid = callback.data.split(':')[1]
        email = await Mail.get(uuid=email_uuid)
        # Здесь реализуйте отправку email через почтовый сервис
        await callback.answer(
            text=f"Response of type '{email.recognized}' sent successfully!"
        )
        await callback.message.edit_reply_markup(reply_markup=None)
        new_text = callback.message.text + "\n\n✅ Response sent!"
        await callback.message.edit_text(
            text=new_text,
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"Error processing response: {e}")
        await callback.answer(
            text=f"Error sending response: {str(e)[:50]}"
        )

async def periodic_check(interval=60):
    while True:
        await check_and_send_notifications()
        await asyncio.sleep(interval)

async def main():
    await init_db()
    await run_migrations()
    asyncio.create_task(periodic_check())
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())