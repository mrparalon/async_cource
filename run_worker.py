import asyncio

from src.tasks.auth_consumer import tasks_auth_worker

if __name__ == "__main__":
    asyncio.run(tasks_auth_worker())
