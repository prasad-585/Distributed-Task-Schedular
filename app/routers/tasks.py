import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.dependencies import get_current_user
from app.models import User, Task, TaskLog, DeadLetterTask
from app.schemas import TaskCreate, TaskUpdate
from app.queue import enqueue_task
from app.rate_limit import rate_limit

router = APIRouter(prefix="/tasks", tags=["Tasks"])

def aware(dt):
    if dt is None:
        return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

@router.post("", dependencies=[Depends(rate_limit)])
def create_task(data: TaskCreate, session: Session = Depends(get_session),
                user: User = Depends(get_current_user)):
    scheduled = aware(data.scheduled_at)
    task = Task(
        user_id=user.id, name=data.name, task_type=data.task_type,
        payload=json.dumps(data.payload), scheduled_at=scheduled,
        priority=data.priority, interval_seconds=data.interval_seconds,
        is_recurring=data.interval_seconds is not None,
        max_retries=data.max_retries,
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    session.add(TaskLog(task_id=task.id, message="Task created"))
    session.commit()
    # return task

    return {
    "id": task.id,
    "user_id": task.user_id,
    "name": task.name,
    "task_type": task.task_type,
    "status": task.status,
    "priority": task.priority
    }


@router.get("")
def list_tasks(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    return session.exec(select(Task).where(Task.user_id == user.id).order_by(Task.created_at.desc())).all()

@router.get("/dead-letter")
def list_dead_letters(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    return session.exec(select(DeadLetterTask).where(DeadLetterTask.user_id == user.id)).all()

@router.get("/{task_id}")
def get_task(task_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    task = session.get(Task, task_id)
    if not task or task.user_id != user.id:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.get("/{task_id}/logs")
def get_logs(task_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    task = session.get(Task, task_id)
    if not task or task.user_id != user.id:
        raise HTTPException(status_code=404, detail="Task not found")
    return session.exec(select(TaskLog).where(TaskLog.task_id == task_id).order_by(TaskLog.created_at)).all()

@router.patch("/{task_id}")
def update_task(task_id: int, data: TaskUpdate, session: Session = Depends(get_session),
                user: User = Depends(get_current_user)):
    task = session.get(Task, task_id)
    if not task or task.user_id != user.id:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status not in ("pending",):
        raise HTTPException(status_code=400, detail="Only pending tasks can be updated")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(task, key, aware(value) if key == "scheduled_at" else value)
    session.add(task)
    session.add(TaskLog(task_id=task.id, message="Task updated"))
    session.commit()
    session.refresh(task)
    return task

@router.post("/{task_id}/cancel")
def cancel_task(task_id: int, session: Session = Depends(get_session),
                user: User = Depends(get_current_user)):
    task = session.get(Task, task_id)
    if not task or task.user_id != user.id:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status in ("completed", "failed", "cancelled"):
        raise HTTPException(status_code=400, detail=f"Task is already {task.status}")
    task.cancel_requested = True
    if task.status in ("pending", "queued"):
        task.status = "cancelled"
    session.add(task)
    session.add(TaskLog(task_id=task.id, message="Cancellation requested"))
    session.commit()
    return {"message": "Cancellation requested", "task_id": task_id}

@router.get("/{task_id}/status")
def task_status(task_id: int, session: Session = Depends(get_session),
                user: User = Depends(get_current_user)):
    task = session.get(Task, task_id)
    if not task or task.user_id != user.id:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"id": task.id, "status": task.status, "priority": task.priority,
            "retry_count": task.retry_count, "error_message": task.error_message}
