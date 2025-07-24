from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise
from tortoise.expressions import Q
from models.mail import Mail
from config import POSTGRES_STR
from models.migrate import run_migrations
import uvicorn
import asyncio
import os
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid as uuid_module
from models.settings import Settings

app = FastAPI()

# CORS setup
cors_mode = os.getenv("CORS_MODE", "")
if cors_mode == "prod":
    origins = ["https://mail.telepat.online"]
else:
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Response models for documentation
class MailResponse(BaseModel):
    from_user: str
    to_user: str
    subject: str
    body: str
    date: datetime
    message_id: str
    attachments_present: bool
    type: str
    recognized: Optional[str]
    pre_generated_answer: Optional[str]

class ChatResponse(BaseModel):
    chat: List[MailResponse]

class SenderInfo(BaseModel):
    uuid: str
    email: str
    unreadCount: int
    lastMessage: Optional[str]
    lastMessageDate: Optional[datetime]

class SendersResponse(BaseModel):
    senders: List[SenderInfo]

class PingResponse(BaseModel):
    message: str

class SettingsResponse(BaseModel):
    gpt_prompt: str
    gpt_model: str
    answers: dict
    types: list

class SettingsUpdateRequest(BaseModel):
    gpt_prompt: Optional[str]
    gpt_model: Optional[str]
    answers: Optional[dict]
    types: Optional[list]

class RegenerateResponse(BaseModel):
    updated: int

@app.get("/ping", response_model=PingResponse)
async def ping():
    return {"message": "Mailer backend is running!"}

@app.get("/senders", response_model=SendersResponse)
async def get_senders():
    # Get all unique senders
    senders = await Mail.filter().distinct().values_list("from_user", flat=True)
    sender_emails = [sender.split("<")[-1].strip(">").strip() for sender in senders]
    sender_emails = set(sender_emails)

    result = []
    for email in sender_emails:
        # Find last message sent by borodin@medsenger.ru to this sender
        last_sent = await Mail.filter(
            from_user__contains="borodin@medsenger.ru", to_user__contains=email
        ).order_by("-date").first()

        last_sent_date = last_sent.date if last_sent else None

        # Count unread messages: messages from sender after last_sent_date
        if last_sent_date:
            unread_count = await Mail.filter(
                from_user__contains=email,
                to_user__contains="borodin@medsenger.ru",
                date__gt=last_sent_date
            ).count()
        else:
            unread_count = await Mail.filter(
                from_user__contains=email,
                to_user__contains="borodin@medsenger.ru"
            ).count()

        # Get last message from sender
        last_msg = await Mail.filter(
            from_user__contains=email,
            to_user__contains="borodin@medsenger.ru"
        ).order_by("-date").first()

        last_message_subject = last_msg.subject if last_msg else None
        last_message_date = last_msg.date if last_msg else None

        result.append(SenderInfo(
            uuid=email,
            email=email,
            unreadCount=unread_count,
            lastMessage=last_message_subject,
            lastMessageDate=last_message_date
        ))

    return {"senders": result}

@app.get("/chat/{sender}", response_model=ChatResponse)
async def get_chat(sender: str):
    if not sender:
        raise HTTPException(status_code=400, detail="Sender cannot be empty")

    chat = await Mail.filter(Q(from_user__contains=sender) | Q(to_user__contains=sender)).order_by("date").values(
        "from_user", "to_user", "subject", "body", "date", "message_id", "attachments_present", "type", "recognized", "pre_generated_answer"
    )

    if not chat:
        raise HTTPException(status_code=404, detail="No messages found for this sender")

    return {"chat": list(chat)}

@app.get("/settings", response_model=SettingsResponse)
async def get_settings():
    settings, _ = await Settings.get_or_create(id=1)
    return {
        "gpt_prompt": settings.gpt_prompt,
        "gpt_model": settings.gpt_model,
        "answers": settings.answers,
        "types": settings.types,
    }

@app.post("/settings", response_model=SettingsResponse)
async def update_settings(update: SettingsUpdateRequest):
    settings, _ = await Settings.get_or_create(id=1)
    if update.gpt_prompt is not None:
        settings.gpt_prompt = update.gpt_prompt
    if update.gpt_model is not None:
        settings.gpt_model = update.gpt_model
    if update.answers is not None:
        settings.answers = update.answers
    if update.types is not None:
        settings.types = update.types
    await settings.save()
    return {
        "gpt_prompt": settings.gpt_prompt,
        "gpt_model": settings.gpt_model,
        "answers": settings.answers,
        "types": settings.types,
    }

@app.post("/regenerate/all", response_model=RegenerateResponse)
async def regenerate_all():
    updated = await Mail.all().update(recognized=None, pre_generated_answer=None)
    return {"updated": updated}

@app.post("/regenerate/{sender}", response_model=RegenerateResponse)
async def regenerate_sender(sender: str):
    updated = await Mail.filter(Q(from_user__contains=sender) | Q(to_user__contains=sender)).update(
        recognized=None, pre_generated_answer=None
    )
    return {"updated": updated}


register_tortoise(
    app,
    db_url=POSTGRES_STR,
    modules={"models": ["models.mail", "models.settings"]},
    generate_schemas=False,
    add_exception_handlers=True,
)

if __name__ == "__main__":
    asyncio.run(run_migrations())
    uvicorn.run("mail_backend.app:app", host="127.0.0.1", port=8000, reload=True)
