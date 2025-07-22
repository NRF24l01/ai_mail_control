import asyncio
from aerich import Command
from .tortoise_config import TORTOISE_ORM

async def run_migrations():
    command = Command(tortoise_config=TORTOISE_ORM, app="models", location="migrations")

    await command.init()
    try:
        await command.init_db(safe=True)
    except Exception as e:
        print(f"[!] DB init skipped or failed: {e}")
    await command.migrate()
    await command.upgrade()

if __name__ == "__main__":
    asyncio.run(run_migrations())
