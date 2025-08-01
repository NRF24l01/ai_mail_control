from tortoise import fields, models

class Mail(models.Model):
    uuid = fields.UUIDField(pk=True)
    from_user = fields.CharField(max_length=255)
    to_user = fields.CharField(max_length=255)
    subject = fields.CharField(max_length=512)
    body = fields.TextField()
    date = fields.DatetimeField()
    message_id = fields.CharField(max_length=255)
    attachments_present = fields.BooleanField()
    type = fields.CharField(max_length=32)
    recognized = fields.CharField(max_length=32, default=None, null=True)
    pre_generated_answer = fields.TextField(default=None, null=True)

class MailNotification(models.Model):
    uuid = fields.UUIDField(pk=True)
    mail = fields.ForeignKeyField('models.Mail', related_name='notifications')
    user_id = fields.BigIntField()  # Telegram user id
    sent_at = fields.DatetimeField(auto_now_add=True)
