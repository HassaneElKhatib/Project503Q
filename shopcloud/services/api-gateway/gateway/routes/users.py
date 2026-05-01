"""User registration, login, profile."""
from __future__ import annotations

import secrets
import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import Order, ReturnRequest, SessionLocal, User, UserProfile
from ..invoice_email import send_login_otp_email
from ..security import (
    hash_password,
    issue_token,
    require_admin,
    require_user,
    verify_password,
)

router = APIRouter()
_mfa_sessions: dict[str, dict[str, str | float]] = {}


async def _session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str = ""


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class GoogleLoginIn(BaseModel):
    googleToken: str


class VerifyOtpIn(BaseModel):
    mfaToken: str
    code: str = Field(min_length=4, max_length=12)


class UpdateMeIn(BaseModel):
    firstName: str | None = None
    lastName: str | None = None
    name: str | None = None
    phone: str | None = None
    image: str | None = None
    password: str | None = Field(default=None, min_length=6)


def _serialize_user(user: User, profile: UserProfile | None = None) -> dict:
    first_name, _, last_name = (user.name or "").partition(" ")
    return {
        "_id": user.id,
        "email": user.email,
        "name": user.name,
        "firstName": first_name,
        "lastName": last_name,
        "role": user.role,
        "isBlocked": user.is_blocked,
        "phone": (profile.phone if profile else "") or "",
        "image": (profile.image if profile else "") or "",
    }


async def _get_or_create_profile(session: AsyncSession, user_id: str) -> UserProfile:
    row = await session.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    profile = row.scalar_one_or_none()
    if profile:
        return profile
    profile = UserProfile(user_id=user_id, phone="", image="")
    session.add(profile)
    await session.flush()
    return profile


@router.post("", status_code=201)
async def register(payload: RegisterIn, session: Annotated[AsyncSession, Depends(_session)]):
    existing = await session.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status.HTTP_409_CONFLICT, detail="email already registered")
    user = User(
        email=payload.email,
        name=payload.name or payload.email.split("@", 1)[0],
        password_hash=hash_password(payload.password),
        role="user",
    )
    session.add(user)
    await session.commit()
    return {"message": "Registration successful! Please login."}


@router.post("/login")
async def login(payload: LoginIn, session: Annotated[AsyncSession, Depends(_session)]):
    row = await session.execute(select(User).where(User.email == payload.email))
    user = row.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    if user.is_blocked:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="account blocked")
    otp_code = f"{secrets.randbelow(1_000_000):06d}"
    mfa_token = secrets.token_urlsafe(24)
    _mfa_sessions[mfa_token] = {
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
        "name": user.name,
        "code": otp_code,
        "expires_at": time.time() + 600,
    }
    email_sent = False
    try:
        email_sent = send_login_otp_email(to_email=user.email, customer_name=user.name, code=otp_code)
    except Exception:
        email_sent = False
    return {
        "mfaRequired": True,
        "mfaToken": mfa_token,
        "email": user.email,
        "emailSent": email_sent,
        "debugOtp": None if email_sent else otp_code,
    }


@router.post("/verify-otp")
async def verify_otp(payload: VerifyOtpIn):
    session_data = _mfa_sessions.get(payload.mfaToken)
    if not session_data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="invalid MFA session")
    if time.time() > float(session_data["expires_at"]):
        _mfa_sessions.pop(payload.mfaToken, None)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="OTP expired")
    if payload.code.strip() != str(session_data["code"]):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="invalid OTP")

    token = issue_token(
        user_id=str(session_data["user_id"]),
        email=str(session_data["email"]),
        role=str(session_data["role"]),
    )
    _mfa_sessions.pop(payload.mfaToken, None)
    return {
        "token": token,
        "role": session_data["role"],
        "name": session_data["name"],
        "email": session_data["email"],
    }


@router.post("/google-login")
async def google_login(_payload: GoogleLoginIn):
    """Google sign-in stub.

    The production path would verify the Google ID token, then upsert a
    user. We intentionally fail loudly so the UI shows a helpful message
    rather than fabricating a user.
    """
    raise HTTPException(
        status.HTTP_501_NOT_IMPLEMENTED,
        detail="Google sign-in is disabled in local mode. Configure VITE_GOOGLE_CLIENT_ID and wire Cognito for production.",
    )


@router.get("/me/")
async def get_me(claims: Annotated[dict, Depends(require_user)], session: Annotated[AsyncSession, Depends(_session)]):
    row = await session.execute(select(User).where(User.id == claims["sub"]))
    user = row.scalar_one_or_none()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="user not found")
    profile = await _get_or_create_profile(session, user.id)
    await session.commit()
    return _serialize_user(user, profile)


@router.put("/")
async def update_me(
    payload: UpdateMeIn,
    claims: Annotated[dict, Depends(require_user)],
    session: Annotated[AsyncSession, Depends(_session)],
):
    row = await session.execute(select(User).where(User.id == claims["sub"]))
    user = row.scalar_one_or_none()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="user not found")
    profile = await _get_or_create_profile(session, user.id)
    if payload.name is not None:
        user.name = payload.name
    else:
        first_name = (payload.firstName or "").strip()
        last_name = (payload.lastName or "").strip()
        joined = f"{first_name} {last_name}".strip()
        if joined:
            user.name = joined
    if payload.phone is not None:
        profile.phone = payload.phone
    if payload.image is not None:
        profile.image = payload.image
    if payload.password:
        user.password_hash = hash_password(payload.password)
    await session.commit()
    await session.refresh(user)
    return _serialize_user(user, profile)


# Admin endpoints used by the UI's user-management screens
@router.get("")
async def admin_list_users(
    _admin: Annotated[dict, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(_session)],
):
    rows = await session.execute(select(User).order_by(User.created_at.desc()))
    profiles = (await session.execute(select(UserProfile))).scalars().all()
    profile_by_user = {p.user_id: p for p in profiles}
    users = []
    for u in rows.scalars():
        first_name, _, last_name = (u.name or "").partition(" ")
        profile = profile_by_user.get(u.id)
        users.append(
            {
                "_id": u.id,
                "email": u.email,
                "name": u.name,
                "firstName": first_name,
                "lastName": last_name,
                "image": (profile.image if profile else "") or "",
                "phone": (profile.phone if profile else "") or "",
                "role": u.role,
                "isBlocked": u.is_blocked,
                "createdAt": u.created_at.isoformat() if u.created_at else None,
            }
        )
    return {"users": users}


@router.put("/{user_id}/block")
async def admin_toggle_block(
    user_id: str,
    _admin: Annotated[dict, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(_session)],
):
    row = await session.execute(select(User).where(User.id == user_id))
    user = row.scalar_one_or_none()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="user not found")
    user.is_blocked = not user.is_blocked
    await session.commit()
    return {"_id": user.id, "isBlocked": user.is_blocked}


@router.get("/{user_id}/details")
async def admin_get_user_details(
    user_id: str,
    _admin: Annotated[dict, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(_session)],
):
    row = await session.execute(select(User).where(User.id == user_id))
    user = row.scalar_one_or_none()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="user not found")

    profile_row = await session.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = profile_row.scalar_one_or_none()

    orders = (
        await session.execute(select(Order).where(Order.user_id == user_id).order_by(Order.created_at.desc()))
    ).scalars().all()
    returns = (
        await session.execute(select(ReturnRequest).where(ReturnRequest.user_id == user_id).order_by(ReturnRequest.created_at.desc()))
    ).scalars().all()
    return {
        "user": _serialize_user(user, profile),
        "orders": [
            {
                "_id": order.id,
                "status": order.status,
                "total": order.total,
                "createdAt": order.created_at.isoformat() if order.created_at else None,
            }
            for order in orders
        ],
        "returns": [
            {
                "_id": ret.id,
                "orderId": ret.order_id,
                "reason": ret.reason,
                "status": ret.status,
                "createdAt": ret.created_at.isoformat() if ret.created_at else None,
                "resolvedAt": ret.resolved_at.isoformat() if ret.resolved_at else None,
            }
            for ret in returns
        ],
    }


@router.delete("/{user_id}")
async def admin_delete_user(
    user_id: str,
    _admin: Annotated[dict, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(_session)],
):
    row = await session.execute(select(User).where(User.id == user_id))
    user = row.scalar_one_or_none()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="user not found")
    await session.delete(user)
    await session.commit()
    return {"message": "user deleted", "_id": user_id}
