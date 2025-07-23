import logging
from tqdm import tqdm
import asyncio
from config import MAIL_HOST, MAIL_USER, MAIL_PASSWORD, DB_PASSWORD


class MailWorker:
    def __init__(self, mail_client, db_client, redis_client):
        self.mail_client = mail_client
        self.db_client = db_client
        self.redis_client = redis_client
        self.logger = logging.getLogger(__name__)

    async def fetch_and_store_new_emails(self):
        try:
            emails = self.mail_client.fetch_threads()
            for email in tqdm(emails, desc="Обработка писем"):
                # print(email)
                try:
                    if self.mail_client.is_spam(email):
                        self.redis_client.set(email["message_id"], email)
                        continue
                    await self.db_client.save_email(email)
                except Exception as e:
                    self.logger.error(f"Ошибка при обработке письма: {e}")
        except Exception as e:
            self.logger.error(f"Ошибка при получении новых писем: {e}")

    async def run(self):
        try:
            print(DB_PASSWORD)
            from models import run_migrations, init_db
            await init_db()
            await run_migrations()
            self.logger.info(1)

            await self.fetch_and_store_new_emails()
        except Exception as e:
            self.logger.critical(f"Критическая ошибка в работе MailWorker: {e}")


if __name__ == "__main__":
    from MailWorker.MailClient import MailClient
    from manage import redis_client, db_client


    mail_client = MailClient(
        host=MAIL_HOST,
        user=MAIL_USER,
        password=MAIL_PASSWORD,
        redis_client=redis_client
    )
    mail = MailWorker(mail_client, db_client, redis_client)
    asyncio.run(mail.run())
