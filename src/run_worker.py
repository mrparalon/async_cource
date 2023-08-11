import asyncio
import logging

from tasks.auth_consumer import tasks_auth_worker

logging.basicConfig(level=logging.INFO)


if __name__ == "__main__":
    asyncio.run(tasks_auth_worker())
