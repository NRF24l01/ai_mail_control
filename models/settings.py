from tortoise import fields, models


class Settings(models.Model):
    id = fields.IntField(pk=True, default=1)
    gpt_prompt = fields.TextField(default="Тебе предложено письмо, твоя задача - определить что это за письмо, варианты: {types}. Если не можешь определить, то ответь 'Undetectable'. Твой ответ долен содержать только одно слово, без кавычек и других символов.")
    gpt_model = fields.CharField(max_length=255, default="gpt-4o-nano")
    answers = fields.JSONField(default={"missmail": "Вам не к нам"})
    types = fields.JSONField(default=["missmail", "spam", "question", "answer", "other"])
