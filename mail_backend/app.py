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


@app.get("/chat/{sender}")
async def get_chat(sender: str):
    if not sender:
        raise HTTPException(status_code=400, detail="Sender cannot be empty")

    chat = await Mail.filter(Q(from_user__contains=sender) | Q(to_user__contains=sender)).order_by("date").values(
        "from_user", "to_user", "subject", "body", "date", "message_id", "attachments_present", "type"
    )

    if not chat:
        raise HTTPException(status_code=404, detail="No messages found for this sender")

    return {"chat": list(chat)}

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
