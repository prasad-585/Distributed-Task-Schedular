from fastapi import Depends, HTTPException
from redis.exceptions import RedisError
from app.dependencies import get_current_user
from app.models import User
from app.redis_client import redis_client

LIMIT = 100
WINDOW_SECONDS = 60

SCRIPT = """
local n = redis.call('INCR', KEYS[1])
if n == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
return n
"""
script = redis_client.register_script(SCRIPT)

def rate_limit(current_user: User = Depends(get_current_user)):
    try:
        count = int(script(keys=[f"rl:user:{current_user.id}"], args=[WINDOW_SECONDS]))
    except RedisError:
        raise HTTPException(status_code=503, detail="Rate limiter unavailable")
    if count > LIMIT:
        raise HTTPException(status_code=429, detail="Rate limit exceeded: 100 requests/minute")
