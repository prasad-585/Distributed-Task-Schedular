from app.redis_client import redis_client, QUEUE_KEY

def enqueue_task(task_id: int, priority: int):
    # Redis sorted set: smaller score means higher priority.
    redis_client.zadd(QUEUE_KEY, {str(task_id): priority})

def pop_task():
    item = redis_client.zpopmin(QUEUE_KEY, count=1)
    if not item:
        return None
    return int(item[0][0])
