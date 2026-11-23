import time
from datetime import datetime, timezone
from sqlmodel import Session, select
from app.database import engine
from app.models import Task, TaskLog
from app.queue import enqueue_task

POLL_SECONDS = 5

def run_scheduler():
    print("Scheduler started")
    while True:
        now = datetime.now(timezone.utc)
        with Session(engine) as session:
            due = session.exec(
                select(Task).where(
                    Task.status == "pending",
                    Task.scheduled_at <= now,
                    Task.cancel_requested == False,  # noqa: E712
                ).order_by(Task.priority, Task.scheduled_at).limit(100)
            ).all()
            for task in due:
                task.status = "queued"
                session.add(task)
                session.add(TaskLog(task_id=task.id, message="Task queued by scheduler"))
            session.commit()
            for task in due:
                enqueue_task(task.id, task.priority)
        time.sleep(POLL_SECONDS)

if __name__ == "__main__":
    run_scheduler()
