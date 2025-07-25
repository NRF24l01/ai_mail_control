from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise
from tortoise.expressions import Q
from models import Mail, User
from config import POSTGRES_STR, MAIL_HOST
from models.migrate import run_migrations
import uvicorn
import asyncio
import os
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid as uuid_module
from models.settings import Settings
import imaplib
from tortoise.transactions import in_transaction
from manage import db_client
from fastapi.responses import JSONResponse
from fastapi.middleware import Middleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

SECRET_KEY = "supersecretkey"


# app = FastAPI()
#
# # Добавляем CORS middleware ПЕРЕД AuthMiddleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # В продакшене замените на конкретные домены
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
#     expose_headers=["*"]  # Важно для CORS
# )

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
    tg_users: List[int]

class SettingsUpdateRequest(BaseModel):
    gpt_prompt: Optional[str]
    gpt_model: Optional[str]
    answers: Optional[dict]
    types: Optional[list]
    tg_users: Optional[List[int]]

class RegenerateResponse(BaseModel):
    updated: int

class AuthRequest(BaseModel):
    email: str
    password: str

class AuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            path = scope["path"]
            # Разрешаем OPTIONS-запросы и запросы к /auth и /ping без авторизации
            if path in ["/auth", "/ping"] or scope["method"] == "OPTIONS":
                await self.app(scope, receive, send)
                return

            # Проверка авторизации для остальных запросов
            headers = dict(scope["headers"])
            token = None
            if b"authorization" in headers:
                auth_header = headers[b"authorization"].decode()
                if auth_header.startswith("Bearer "):
                    token = auth_header.split("Bearer ", 1)[1]
            if not token:
                response = JSONResponse({"detail": "Unauthorized"}, status_code=401)
                await response(scope, receive, send)
                return
            try:
                jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            except Exception:
                response = JSONResponse({"detail": "Invalid token"}, status_code=401)
                await response(scope, receive, send)
                return
        await self.app(scope, receive, send)

# app.add_middleware(AuthMiddleware)


from fastapi.middleware import Middleware

middleware = [
    Middleware(CORSMiddleware, allow_origins=["*"],  # ← замените на конкретные домены в проде
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"]),
    Middleware(AuthMiddleware)
]
app = FastAPI(middleware=middleware)

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
        # Find last message sent by borodin@medsenger.ru or support@medsenger.ru to this sender
        last_sent = await Mail.filter(
            Q(from_user__contains="borodin@medsenger.ru") | Q(from_user__contains="support@medsenger.ru"),
            to_user__contains=email
        ).order_by("-date").first()

        last_sent_date = last_sent.date if last_sent else None

        # Count unread messages: messages from sender after last_sent_date
        if last_sent_date:
            unread_count = await Mail.filter(
                Q(to_user__contains="borodin@medsenger.ru") | Q(to_user__contains="support@medsenger.ru"),
                from_user__contains=email,
                date__gt=last_sent_date
            ).count()
        else:
            unread_count = await Mail.filter(
                Q(to_user__contains="borodin@medsenger.ru") | Q(to_user__contains="support@medsenger.ru"),
                from_user__contains=email
            ).count()

        # Get last message from sender
        last_msg = await Mail.filter(
            Q(to_user__contains="borodin@medsenger.ru") | Q(to_user__contains="support@medsenger.ru"),
            from_user__contains=email
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
        "tg_users": settings.tg_users,
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
    if update.tg_users is not None:
        settings.tg_users = update.tg_users
    await settings.save()
    return {
        "gpt_prompt": settings.gpt_prompt,
        "gpt_model": settings.gpt_model,
        "answers": settings.answers,
        "types": settings.types,
        "tg_users": settings.tg_users,
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

@app.post("/auth")
async def auth(data: AuthRequest):
    email = data.email
    password = data.password
    try:
        mail = imaplib.IMAP4_SSL(MAIL_HOST, timeout=20)
        mail.login(email, password)
        mail.logout()
    except Exception as e:
        # Возвращаем явный JSONResponse с кодом 401
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Неверная почта или пароль"}
        )

    await db_client.add_user(email, password)
    # Генерируем JWT токен
    token = jwt.encode({"email": email}, SECRET_KEY, algorithm="HS256")
    return {"success": True, "token": token}


register_tortoise(
    app,
    db_url=POSTGRES_STR,
    modules={"models": ["models.mail", "models.settings", "models.user"]},
    generate_schemas=False,
    add_exception_handlers=True,
)

if __name__ == "__main__":
    asyncio.run(run_migrations())
    uvicorn.run("mail_backend.app:app", host="127.0.0.1", port=8000, reload=True)
