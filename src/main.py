import asyncio

from fastapi import FastAPI

from src.auth.router import router as auth_router
from src.tasks.auth_consumer import tasks_auth_worker
from src.tasks.router import router as tasks_router

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    app.state.workers = {
        "tasks_auth": asyncio.create_task(tasks_auth_worker()),
    }


app.include_router(auth_router, tags=["auth"])
app.include_router(tasks_router, tags=["tasks"])
