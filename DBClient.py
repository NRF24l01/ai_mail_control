from models import Mail
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
