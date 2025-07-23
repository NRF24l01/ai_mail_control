import logging
from tqdm import tqdm
import asyncio
from config import MAIL_HOST, MAIL_USER, MAIL_PASSWORD, DB_PASSWORD, DB_DATABASE, DB_HOST, DB_PORT
import json
import asyncio
from MailWorker.MailClient import MailClient
from manage import redis_client, db_client
import time

class MailWorker:
    def __init__(self, mail_client, db_client, redis_client):
        self.mail_client = mail_client
        self.db_client = db_client
        self.redis_client = redis_client
        self.logger = logging.getLogger(__name__)

    def _clean_bytes(self, obj):
        if isinstance(obj, dict):
            return {k: self._clean_bytes(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._clean_bytes(i) for i in obj]
        elif isinstance(obj, bytes):
            try:
                return obj.decode('utf-8', errors='ignore')
            except:
                return str(obj)
        else:
            return obj

    async def fetch_and_store_new_emails(self):
        try:
            emails = self.mail_client.fetch_threads()
            for email in tqdm(emails, desc="Обработка писем"):
                try:
                    if await self.mail_client.is_spam(email):
                        if isinstance(email, bytes):
                            email = json.loads(email.decode("utf-8"))
                        cleaned_email = self._clean_bytes(email)
                        self.redis_client.set(email["message_id"], json.dumps(cleaned_email, ensure_ascii=False))
                        continue

                    await self.db_client.save_email(email)
                except Exception as e:
                    self.logger.error(f"Ошибка при обработке письма: {e}")
        except Exception as e:
            self.logger.error(f"Ошибка при получении новых писем: {e}")

    async def run(self):
        try:
            from models import run_migrations, init_db
            await init_db()
            await run_migrations()
            await self.fetch_and_store_new_emails()
        except Exception as e:
            self.logger.critical(f"Критическая ошибка в работе MailWorker: {e}")


async def periodic_run():
    while True:
        await mail.run()
        print("Почта проверена, ждем 10 минут...")
        await asyncio.sleep(600)  # 10 минут

if __name__ == "__main__":
    mail_client = MailClient(
        host=MAIL_HOST,
        user=MAIL_USER,
        password=MAIL_PASSWORD,
        redis_client=redis_client
    )
    mail = MailWorker(mail_client, db_client, redis_client)

    asyncio.run(periodic_run())
