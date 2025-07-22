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


def main():
    try:
        asyncio.run(run_migrations())
    except RuntimeError:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            task = loop.create_task(run_migrations())
            import time
            while not task.done():
                time.sleep(0.1)
        else:
            loop.run_until_complete(run_migrations())


if __name__ == "__main__":
    main()
