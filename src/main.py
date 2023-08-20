import asyncio

from fastapi import FastAPI

from src.accounting.auth_consumer import accounting_auth_worker
from src.accounting.tasks_biz_consumer import accounting_tasks_lificycle_worker
from src.auth.router import router as auth_router
from src.tasks.auth_consumer import tasks_auth_worker
from src.tasks.router import router as tasks_router

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    app.state.workers = {
        "tasks_auth": asyncio.create_task(tasks_auth_worker()),
        "accounting_auth": asyncio.create_task(accounting_auth_worker()),
        "accounting_tasks_biz": asyncio.create_task(accounting_tasks_lificycle_worker()),
    }


@app.on_event("shutdown")
async def shutdown_event():
    for worker in app.state.workers.values():
        worker.cancel()


app.include_router(auth_router, tags=["auth"])
app.include_router(tasks_router, tags=["tasks"])
