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
