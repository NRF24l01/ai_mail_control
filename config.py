import os
from dotenv import load_dotenv

if os.getenv("PROD_MODE", "") != "true":
    load_dotenv()


DB_LOGIN=os.getenv("DB_LOGIN")
DB_PASSWORD=os.getenv("DB_PASSWORD")
DB_HOST=os.getenv("DB_HOST")
DB_PORT=os.getenv("DB_PORT")
DB_DATABASE=os.getenv("DB_DATABASE")


POSTGRES_STR = f"postgres://{DB_LOGIN}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}"

MAIL_HOST = os.getenv("MAIL_HOST")
MAIL_USER = os.getenv("MAIL_USER")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")