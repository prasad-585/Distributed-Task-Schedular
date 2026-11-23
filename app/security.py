from datetime import datetime, timedelta, timezone
import jwt
from pwdlib import PasswordHash
from app.config import SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_MINUTES

password_hash = PasswordHash.recommended()

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)

def create_access_token(user_id: int) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_MINUTES)
    return jwt.encode(
        {"sub": str(user_id), "exp": expires},
        SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )
