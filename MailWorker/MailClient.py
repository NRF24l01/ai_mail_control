import imaplib
import email
from email.header import decode_header
from email.utils import parsedate_tz, mktime_tz
from datetime import datetime
import os
import time
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
import threading
from manage import redis_client
from config import MAIL_HOST, MAIL_USER, MAIL_PASSWORD

class MailClient:
    def __init__(self, host, user, password, redis_client, max_workers=15, output_dir="emails"):
        self.host = host
        self.user = user
        self.password = password
        self.max_workers = max_workers
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.attachments_map = {}
        self.redis = redis_client
        self._last_seen_ids_key = "mail:last_seen_ids"

    def _connect(self):
        mail = imaplib.IMAP4_SSL(self.host)
        mail.login(self.user, self.password)
        return mail

    def _decode_header(self, val):
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
        date_tuple = parsedate_tz(msg.get("Date"))
        return datetime.fromtimestamp(mktime_tz(date_tuple)) if date_tuple else None

    def _get_thread_id(self, msg):
        return msg.get("References") or msg.get("In-Reply-To") or msg.get("Message-ID")

    def _extract_body_attachments(self, msg):
        body, attachments = "", []
        is_multipart = msg.is_multipart()
        parts = msg.walk() if is_multipart else [msg]

        for part in parts:
            ctype = part.get_content_type()
            disp = str(part.get("Content-Disposition"))
            charset = part.get_content_charset() or "utf-8"
            if charset.lower() in ("unknown-8bit", "unknown"):
                charset = "utf-8"

            if ctype == "text/plain" and "attachment" not in disp:
                payload = part.get_payload(decode=True)
                body = payload.decode(charset, errors="replace") if payload else ""
            elif part.get_filename():
                filename = self._decode_header(part.get_filename())
                attachments.append({"filename": filename, "payload": part.get_payload(decode=True)})

        to_field = self._decode_header(msg.get("To", ""))
        return body, attachments, bool(attachments), to_field

    def _fetch_uids(self, mail, folder):
        if mail.select(folder)[0] != "OK":
            return []
        status, data = mail.search(None, '(SINCE "01-Jan-2025")')
        return data[0].split() if status == "OK" else []

    def _process_email(self, idx, folder, uid, threads_dict, lock):
        try:
            for _ in range(3):
                try:
                    mail = self._connect()
                    mail.select(folder)
                    status, msg_data = mail.fetch(uid, "(RFC822)")
                    mail.logout()
                    if status != "OK":
                        raise Exception("Fetch failed")
                    break
                except (imaplib.IMAP4.abort, imaplib.IMAP4.error, OSError):
                    time.sleep(2)
            else:
                raise Exception("Fetch failed after retries")

            for part in msg_data:
                if isinstance(part, tuple):
                    msg = email.message_from_bytes(part[1])
                    dt = self._get_date(msg)
                    if not dt or dt.year < 2025:
                        return

                    subject = self._decode_header(msg["Subject"])
                    sender = self._decode_header(msg.get("From"))
                    date_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                    body, attachments, has_attachments, to_field = self._extract_body_attachments(msg)
                    thread_id = self._get_thread_id(msg) or f"{folder}_{idx}"
                    origin = "inbox" if folder.upper() == "INBOX" else "sent"

                    message_id = (msg.get("Message-ID") or "").strip()
                    redis_key = f"mail:{message_id}"
                    if self.redis.exists(redis_key):
                        return

                    email_key = (subject, sender, date_str, folder)
                    if has_attachments:
                        self.attachments_map[email_key] = attachments

                    email_data = {
                        "idx": idx,
                        "folder": folder,
                        "origin": origin,
                        "subject": subject,
                        "from": sender,
                        "to": to_field,
                        "date_str": date_str,
                        "body": body,
                        "attachments_present": has_attachments,
                        "message_id": message_id
                    }

                    with lock:
                        threads_dict[thread_id.strip()].append(email_data)

        except Exception as e:
            self._log_error(f"{folder}:{idx}", str(e))

    def _log_error(self, context, error_msg):
        with open(os.path.join(self.output_dir, "errors.log"), "a", encoding="utf-8") as f:
            f.write(f"[{context}] {error_msg}\n")

    def is_spam(self, msg):
        """
        Проверяет письмо на спам по простым признакам:
        - наличие заголовка 'X-Spam-Flag: YES'
        - наличие слова 'spam' в теме (без учета регистра)
        Можно расширить по необходимости.
        """
        spam_flag = msg.get('X-Spam-Flag', '').lower()
        subject = self._decode_header(msg.get('Subject', '')).lower()
        if spam_flag == 'yes':
            return True
        if 'spam' in subject:
            return True
        return False

    def fetch_threads(self):
        folders = ["INBOX", "Sent", "Отправленные", "[Gmail]/Sent Mail"]
        threads_dict = defaultdict(list)
        tasks, lock = [], threading.Lock()

        cached_ids = set()
        cached_emails = {}
        if self.redis.exists(self._last_seen_ids_key):
            cached_ids = set(self.redis.smembers(self._last_seen_ids_key))
            cached_ids = {cid.decode() if isinstance(cid, bytes) else cid for cid in cached_ids}
            for cid in cached_ids:
                cached_email = self.redis.get(f"mail:cache:{cid}")
                if cached_email:
                    try:
                        import json
                        cached_emails[cid] = json.loads(cached_email)
                    except Exception:
                        pass

        new_ids = set()

        for folder in folders:
            try:
                mail = self._connect()
                uids = self._fetch_uids(mail, folder)
                mail.logout()
                tasks += [(i, folder, uid, threads_dict, lock) for i, uid in enumerate(uids, 1)]
            except Exception as e:
                self._log_error(f"{folder}:uids", str(e))

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            list(tqdm(executor.map(lambda args: self._process_email(*args), tasks), total=len(tasks), desc="Обработка писем"))

        all_emails = []
        for emails in threads_dict.values():
            for email in emails:
                msg_id = email.get("message_id", "")
                if msg_id:
                    if msg_id in cached_ids and msg_id in cached_emails:
                        all_emails.append(cached_emails[msg_id])
                    else:
                        all_emails.append(email)
                        new_ids.add(msg_id)
                        try:
                            import json
                            self.redis.set(f"mail:cache:{msg_id}", json.dumps(email, ensure_ascii=False))
                        except Exception:
                            pass

        for cid in cached_ids:
            if cid not in {e.get("message_id", "") for e in all_emails} and cid in cached_emails:
                all_emails.append(cached_emails[cid])

        all_emails_sorted = sorted(all_emails, key=lambda x: x["date_str"])

        if new_ids:
            self.redis.sadd(self._last_seen_ids_key, *new_ids)

        return all_emails_sorted


if __name__ == "__main__":
    client = MailClient(
        host=MAIL_HOST,
        user=MAIL_USER,
        password=MAIL_PASSWORD,
        redis_client=redis_client
    )
    emails = client.fetch_threads()
    print(f"Писем: {len(emails)}")
    for email in emails:
        print(email)
