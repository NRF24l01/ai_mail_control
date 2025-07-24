import imaplib
import email
from email.header import decode_header
from email.utils import parsedate_tz, mktime_tz
import os
import time
import json
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
import threading
from manage import redis_client
from config import MAIL_HOST, MAIL_USER, MAIL_PASSWORD
import aiospamc
from email.utils import format_datetime
from datetime import datetime
from bs4 import BeautifulSoup

class MailClient:
    """
    Клиент для работы с почтовым сервером через IMAP.
    Поддерживает многопоточное скачивание писем, определение спама,
    хранение в Redis и обработку вложений.
    """

    def __init__(self, host, user, password, redis_client, max_workers=60, output_dir="emails"):
        self.host = host
        self.user = user
        self.password = password
        self.max_workers = max_workers
        self.output_dir = output_dir
        self.redis = redis_client
        self._last_seen_ids_key = "mail:last_seen_ids"
        self.attachments_map = {}

        os.makedirs(output_dir, exist_ok=True)

    def _connect(self):
        """Создает IMAP соединение"""
        mail = imaplib.IMAP4_SSL(self.host)
        mail.login(self.user, self.password)
        return mail

    def _fetch_uids(self, mail, folder):
        """Получает список UID писем из указанной папки начиная с 20 июля 2025"""
        if mail.select(folder)[0] != "OK":
            return []
        status, data = mail.search(None, '(SINCE "20-Jul-2025")')
        return data[0].split() if status == "OK" else []

    # --- Парсинг заголовков и содержимого ---

    def _decode_header(self, val):
        """Декодирует заголовок письма из различных кодировок"""
        if not val:
            return ""

        decoded = ""
        for part, encoding in decode_header(val):
            enc = (encoding or "utf-8").lower()
            if enc in ("unknown-8bit", "unknown", None):
                enc = "utf-8"
            decoded += part.decode(enc, errors="replace") if isinstance(part, bytes) else part
        return decoded

    def _get_date(self, msg):
        """Извлекает и преобразует дату письма"""
        date_tuple = parsedate_tz(msg.get("Date"))
        return datetime.fromtimestamp(mktime_tz(date_tuple)) if date_tuple else None

    def _get_thread_id(self, msg):
        """Определяет ID цепочки сообщений"""
        return msg.get("References") or msg.get("In-Reply-To") or msg.get("Message-ID")

    def _extract_body_attachments(self, msg):
        """Извлекает тело письма, вложения и другие метаданные.
        Если есть html, парсит его в текст и очищает от лишних символов.
        """
        body = ""
        html_body = None
        attachments = []
        content_type = "text/plain"
        charset = "utf-8"

        for part in msg.walk():
            ctype = part.get_content_type()
            content_type = ctype
            disp = str(part.get("Content-Disposition"))
            charset = part.get_content_charset() or "utf-8"

            if charset.lower() in ("unknown-8bit", "unknown"):
                charset = "utf-8"

            if ctype == "text/plain" and "attachment" not in disp:
                payload = part.get_payload(decode=True)
                body = payload.decode(charset, errors="replace") if payload else ""
            elif ctype == "text/html" and "attachment" not in disp:
                payload = part.get_payload(decode=True)
                if payload:
                    html_body = payload.decode(charset, errors="replace")
            elif part.get_filename():
                filename = self._decode_header(part.get_filename())
                attachments.append({"filename": filename, "payload": part.get_payload(decode=True)})

        if html_body:
            try:
                soup = BeautifulSoup(html_body, "lxml")
                text = soup.get_text(separator="\n", strip=True)
                if text.strip():
                    body = text
                    content_type = "text/plain"
            except Exception as e:
                self._log_error("html_parse", str(e))

        to_field = self._decode_header(msg.get("To", ""))
        has_attachments = bool(attachments)

        return body, attachments, has_attachments, to_field, content_type, charset

    def _process_email(self, idx, folder, uid, threads_dict, lock):
        """Обрабатывает одно письмо"""
        try:
            msg = self._fetch_message(idx, folder, uid)
            if not msg:
                return

            dt = self._get_date(msg)
            if not dt or dt.year < 2025:
                return

            subject = self._decode_header(msg["Subject"])
            sender = self._decode_header(msg.get("From"))
            date_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            body, attachments, has_attachments, to_field, content_type, charset = self._extract_body_attachments(msg)

            thread_id = self._get_thread_id(msg)
            origin = "inbox" if folder.upper() == "INBOX" else "sent"
            message_id = (msg.get("Message-ID") or "").strip()

            redis_key = f"mail:{message_id}"
            if self.redis.exists(redis_key):
                return

            if has_attachments:
                email_key = (subject, sender, date_str, folder)
                self.attachments_map[email_key] = attachments

            email_data = {
                "idx": idx,
                "uid": uid,
                "folder": folder,
                "origin": origin,
                "subject": subject,
                "from": sender,
                "to": to_field,
                "date_str": date_str,
                "body": body,
                "attachments_present": has_attachments,
                "message_id": message_id,
                "content_type": content_type,
                "charset": charset
            }

            with lock:
                threads_dict[thread_id.strip()].append(email_data)

        except Exception as e:
            self._log_error(f"{folder}:{idx}", str(e))

    def _fetch_message(self, idx, folder, uid):
        """Получает сообщение из IMAP с повторными попытками"""
        for _ in range(3):
            try:
                mail = self._connect()
                mail.select(folder)
                status, msg_data = mail.fetch(uid, "(RFC822)")
                mail.logout()

                if status != "OK":
                    raise Exception("Fetch failed")

                for part in msg_data:
                    if isinstance(part, tuple):
                        return email.message_from_bytes(part[1])

                return None

            except (imaplib.IMAP4.abort, imaplib.IMAP4.error, OSError):
                time.sleep(2)

        raise Exception("Fetch failed after retries")

    async def is_spam(self, email) -> bool:
        """
        score — оценка spamassassin
        body, subject — текст письма
        """
        score = await self.analise_mail(email)

        if score < 9.0:
            return True  # явно спам

        elif score >= 9.0:
            return False

    async def analise_mail(self, raw_email):
        """
        Проверяет письмо на спам через SpamAssassin.
        Принимает словарь email_data или строку с текстом письма.
        """
        try:
            raw_email_str = self._prepare_email_for_spam_check(raw_email)
            raw_email_bytes = raw_email_str.encode('utf-8')
            content_length = len(raw_email_bytes)
            request_headers = (
                f"SYMBOLS SPAMC/1.5\r\n"
                f"Content-length: {content_length}\r\n"
                f"\r\n"
            ).encode('utf-8')
            request = request_headers + raw_email_bytes

            score = await aiospamc.check(request, host='spamassassin')
            return score.headers.spam.score if score.headers.spam else 0.0

        except Exception as e:
            print(f"Error checking spam score: {e}")


    def _prepare_email_for_spam_check(self, raw_email):
        if isinstance(raw_email, dict):
            subject = raw_email.get('subject', '')
            body = raw_email.get('body', '')
            from_ = raw_email.get('from', '')
            to_ = raw_email.get('to', '')
            date_str = raw_email.get('date_str', '')
            message_id = raw_email.get('message_id', '')
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                date_formatted = format_datetime(dt)
            except Exception:
                date_formatted = date_str
            return (
                f"Message-ID: {message_id}\r\n"
                f"Date: {date_formatted}\r\n"
                f"From: {from_}\r\n"
                f"To: {to_}\r\n"
                f"Subject: {subject}\r\n"
                "MIME-Version: 1.0\r\n"                
                f"Content-Type: {raw_email.get('content_type', 'text/plain')}; "
                f"\r\n"
                f"{body}"
            )
        else:
            return str(raw_email)
    # --- Основные методы для получения писем ---

    def fetch_threads(self):
        """
        Получает письма из всех папок и группирует их в цепочки.
        Учитывает кэширование в Redis для ускорения повторной загрузки.
        """
        # Папки для проверки
        folders = ["INBOX", "Sent", "Отправленные", "[Gmail]/Sent Mail"]
        threads_dict = defaultdict(list)
        tasks = []
        lock = threading.Lock()

        # Получение кэшированных ID из Redis
        cached_ids = self._get_cached_ids()
        new_ids = set()

        # Получение списка задач для обработки
        for folder in folders:
            try:
                mail = self._connect()
                uids = self._fetch_uids(mail, folder)

                mail.logout()
                for i, uid in enumerate(uids, 1):
                    if isinstance(uid, bytes):
                        uid = uid.decode()

                    if uid not in cached_ids:
                        obj = (i, folder, uid, threads_dict, lock)
                        tasks.append(obj)

            except Exception as e:
                self._log_error(f"{folder}:uids", str(e))

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            list(tqdm(executor.map(lambda args: self._process_email(*args), tasks),
                      total=len(tasks), desc="Обработка писем"))

        all_emails = []
        for emails in threads_dict.values():
            for email in emails:

                all_emails.append(email)
                msg_id = email.get("message_id", "")
                if msg_id:
                    new_ids.add(email.get("uid", ""))
                    try:
                        self.redis.set(f"mail:cache:{msg_id}", json.dumps(email, ensure_ascii=False))
                    except Exception as e:
                        self._log_error("redis_cache", str(e))

        all_emails_sorted = sorted(all_emails, key=lambda x: x["date_str"])

        if new_ids:
            self.redis.sadd(self._last_seen_ids_key, *new_ids)

        return all_emails_sorted

    def _get_cached_ids(self):
        if self.redis.exists(self._last_seen_ids_key):
            cached_ids = set(self.redis.smembers(self._last_seen_ids_key))
            return [cid.decode() if isinstance(cid, bytes) else cid for cid in cached_ids]
        return set()

    def _log_error(self, context, error_msg):
        """Логирует ошибки в файл"""
        with open(os.path.join(self.output_dir, "errors.log"), "a", encoding="utf-8") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] [{context}] {error_msg}\n")


if __name__ == "__main__":
    client = MailClient(
        host=MAIL_HOST,
        user=MAIL_USER,
        password=MAIL_PASSWORD,
        redis_client=redis_client
    )
    emails = client.fetch_threads()
    print(f"Получено писем: {len(emails)}")
