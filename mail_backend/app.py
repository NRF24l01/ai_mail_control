from fastapi import FastAPI, HTTPException
from tortoise.contrib.fastapi import register_tortoise
from tortoise.expressions import Q
from models.mail import Mail
from config import POSTGRES_STR
from models.migrate import run_migrations
import uvicorn
import asyncio

app = FastAPI()

@app.get("/senders")
async def get_senders():
    senders = await Mail.filter().distinct().values_list("from_user", flat=True)
    out = [sender.split("<")[-1].strip(">").strip() for sender in senders]
    return {"senders": out}

register_tortoise(
    app,
    db_url=POSTGRES_STR,
    modules={"models": ["models.mail"]},
    generate_schemas=False,
    add_exception_handlers=True,
)

if __name__ == "__main__":
    asyncio.run(run_migrations())
    uvicorn.run("mail_backend.app:app", host="127.0.0.1", port=8000, reload=True)
