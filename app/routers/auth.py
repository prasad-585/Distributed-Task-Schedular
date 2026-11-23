from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.models import User
from app.schemas import RegisterIn, LoginIn, TokenOut
from app.security import hash_password, verify_password, create_access_token
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=dict)
def register(data: RegisterIn, session: Session = Depends(get_session)):
    existing = session.exec(select(User).where(User.email == data.email)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(email=data.email, password_hash=hash_password(data.password))
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"id": user.id, "email": user.email}

# @router.post("/login", response_model=TokenOut)
# def login(data: LoginIn, session: Session = Depends(get_session)):
#     user = session.exec(select(User).where(User.email == data.email)).first()
#     if not user or not verify_password(data.password, user.password_hash):
#         raise HTTPException(status_code=401, detail="Invalid email or password")
#     return TokenOut(access_token=create_access_token(user.id))


@router.post("/login", response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends(),
          session: Session = Depends(get_session)):

    user = session.exec(
        select(User).where(User.email == form.username)
    ).first()

    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")

    return TokenOut(access_token=create_access_token(user.id))