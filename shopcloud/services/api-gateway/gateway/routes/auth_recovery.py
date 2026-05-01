"""Password recovery stubs.

Real implementations issue an email via SES with a one-time code. The
stub stores codes in memory and returns them in the response so a
developer can complete the flow without an email gateway.
"""
from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import SessionLocal, User
from ..invoice_email import send_password_reset_code_email
from ..security import hash_password
from ..settings import settings

router = APIRouter()

_codes: dict[str, str] = {}


async def _session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session


class ForgotIn(BaseModel):
    email: EmailStr


class ResetIn(BaseModel):
    email: EmailStr
    code: str
    password: str = Field(min_length=6)


@router.post("/forgot-password")
async def forgot_password(payload: ForgotIn, session: Annotated[AsyncSession, Depends(_session)]):
    if not settings.use_local_gateway_auth:
        raise HTTPException(
            status.HTTP_410_GONE,
            detail="Use Cognito hosted UI (Forgot password) instead.",
        )
    row = await session.execute(select(User).where(User.email == payload.email))
    user = row.scalar_one_or_none()
    if not user:
        # Avoid leaking which emails are registered.
        return {"message": "if the email exists, a reset code has been sent"}
    code = secrets.token_hex(4)
    _codes[payload.email] = code
    emailed = False
    try:
        emailed = send_password_reset_code_email(to_email=user.email, customer_name=user.name, code=code)
    except Exception:
        emailed = False
    response = {"message": "if the email exists, a reset code has been sent", "emailSent": emailed}
    if not emailed:
        # Keep local recovery usable when SMTP is not configured.
        response["debug_code"] = code
    return response


@router.post("/reset-password")
async def reset_password(payload: ResetIn, session: Annotated[AsyncSession, Depends(_session)]):
    if not settings.use_local_gateway_auth:
        raise HTTPException(
            status.HTTP_410_GONE,
            detail="Use Cognito hosted UI (Forgot password) instead.",
        )
    expected = _codes.get(payload.email)
    if not expected or expected != payload.code:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="invalid reset code")
    row = await session.execute(select(User).where(User.email == payload.email))
    user = row.scalar_one_or_none()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="user not found")
    user.password_hash = hash_password(payload.password)
    await session.commit()
    _codes.pop(payload.email, None)
    return {"message": "password reset"}
