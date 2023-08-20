import asyncio

from src.accounting.end_day_script import end_day

if __name__ == "__main__":
    asyncio.run(end_day())
