import json
import time
from datetime import datetime, timezone, timedelta
from sqlmodel import Session
from app.database import engine
from app.models import Task, TaskLog, DeadLetterTask
from app.queue import pop_task

def execute_demo(task: Task):
    # Replace this with real task handlers (email, report, etc.).
    print(f"Executing [{task.task_type}] task #{task.id}: {task.name}")
    payload = json.loads(task.payload or "{}")
    print("Payload:", payload)
    time.sleep(1)

def process_task(task_id: int):
    with Session(engine) as session:
        task = session.get(Task, task_id)
        if not task or task.status != "queued":
            return
        # Atomic claim: only one worker can change queued -> running.
        task.status = "running"
        task.started_at = datetime.now(timezone.utc)
        session.add(task)
        session.add(TaskLog(task_id=task.id, message="Worker started task"))
        session.commit()

    try:
        with Session(engine) as session:
            task = session.get(Task, task_id)
            if task.cancel_requested:
                task.status = "cancelled"
                session.add(task)
                session.add(TaskLog(task_id=task.id, message="Task cancelled before execution"))
                session.commit()
                return
            execute_demo(task)
            task.completed_at = datetime.now(timezone.utc)
            if task.is_recurring and task.interval_seconds:
                task.status = "pending"
                task.scheduled_at = task.completed_at + timedelta(seconds=task.interval_seconds)
                task.retry_count = 0
                task.cancel_requested = False
                task.started_at = None
                task.completed_at = None
                session.add(TaskLog(task_id=task.id, message="Recurring task rescheduled"))
            else:
                task.status = "completed"
                session.add(TaskLog(task_id=task.id, message="Task completed"))
            session.add(task)
            session.commit()
    except Exception as exc:
        with Session(engine) as session:
            task = session.get(Task, task_id)
            if not task:
                return
            task.error_message = str(exc)
            task.retry_count += 1
            if task.retry_count <= task.max_retries:
                task.status = "pending"
                task.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=2 ** task.retry_count)
                task.scheduled_at = task.next_retry_at
                session.add(TaskLog(task_id=task.id, message=f"Retry scheduled: {exc}"))
            else:
                task.status = "failed"
                session.add(DeadLetterTask(
                    original_task_id=task.id, user_id=task.user_id,
                    task_name=task.name, error_message=str(exc),
                    retry_count=task.retry_count,
                ))
                session.add(TaskLog(task_id=task.id, message="Moved to dead-letter queue"))
            session.add(task)
            session.commit()

def run_worker():
    print("Worker started")
    while True:
        try:
            task_id = pop_task()
            if task_id is None:
                time.sleep(1)
                continue
            process_task(task_id)
        except Exception as exc:
            print("Worker loop error:", exc)
            time.sleep(3)

if __name__ == "__main__":
    run_worker()
