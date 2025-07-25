from config import POSTGRES_STR

TORTOISE_ORM = {
    "connections": {
        "postgres": POSTGRES_STR
    },
    "apps": {
        "models": {
            "models": ["models", "aerich.models", "models.mail", "models.settings"],
            "default_connection": "postgres",
        },
    },
}
