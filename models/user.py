from tortoise import fields, models

class User(models.Model):
    uuid = fields.UUIDField(pk=True)
    email = fields.CharField(max_length=255, unique=True, default="")
    password = fields.CharField(max_length=255, default="")

    def __str__(self):
        return self.email
