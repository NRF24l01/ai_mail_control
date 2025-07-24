from models import Mail, Settings
from tortoise.transactions import in_transaction


class DBClient:
    async def save_email(self, email):
        async with in_transaction():
            await Mail.create(
                from_user=email.get("from", ""),
                to_user=email.get("to", ""),
                subject=email.get("subject", ""),
                body=email.get("body", ""),
                date=email.get("date_str"),
                message_id=email.get("message_id", ""),
                attachments_present=email.get("attachments_present", False),
                type=email.get("folder", "")
            )

    async def get_unprocessed_emails(self):
        async with in_transaction():
            # Get all INBOX emails with recognized=None
            inbox_emails = await Mail.filter(type="INBOX", recognized=None).all()
            result = []
            for email in inbox_emails:
                # Find the latest email in the conversation with this author (from_user)
                latest_email = await Mail.filter(
                    from_user=email.from_user
                ).order_by('-date').first()
                # If the latest email is this one and it's INBOX, or if the latest is SENT, include
                if latest_email and (
                    (latest_email.uuid == email.uuid and latest_email.type == "INBOX") and
                    (latest_email.type != "SENT")
                ):
                    result.append(email)
            return result
    
    async def mark_email_as_processed(self, email_id, type, answer=None):
        async with in_transaction():
            email = await Mail.get(uuid=email_id)
            email.recognized = type
            if answer:
                email.pre_generated_answer = answer
            await email.save()
    
    async def get_settings(self):
        async with in_transaction():
            settings, _=  await Settings.get_or_create(id=1)
            return settings

    async def email_exists(self, email):
        """
        Проверяет, есть ли письмо в базе по message_id.
        Возвращает True, если письмо найдено, иначе False.
        """
        async with in_transaction():
            message_id = email.get("message_id", "")
            exists = await Mail.filter(message_id=message_id).exists()
            return exists
