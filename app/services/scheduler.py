import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from app.services.publisher import execute_idempotent_publish
from app.core.database import DB_PATH

# Configure persistent job store using SQLite so jobs survive restarts
jobstores = {
    'default': SQLAlchemyJobStore(url=f'sqlite:///{DB_PATH}')
}

scheduler = AsyncIOScheduler(jobstores=jobstores)

def sync_publish_wrapper(slot_id: int):
    """Bridge sync APScheduler execution to async publisher engine."""
    asyncio.run(execute_idempotent_publish(slot_id))

def start_scheduler():
    if not scheduler.running:
        scheduler.start()
        print("Durable APScheduler started with SQLite job store.")

def schedule_job_execution(slot_id: int, run_time):
    """Enqueues job into persistent SQLite store."""
    scheduler.add_job(
        sync_publish_wrapper,
        'date',
        run_date=run_time,
        args=[slot_id],
        id=f"job_slot_{slot_id}",
        replace_existing=True
    )