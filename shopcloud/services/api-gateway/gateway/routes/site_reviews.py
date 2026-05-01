"""Site-wide reviews (testimonials)."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import SessionLocal, SiteReview, User
from ..security import require_admin, require_user

router = APIRouter()


async def _session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session


class SiteReviewIn(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str = ""


class StatusIn(BaseModel):
    isApproved: bool


async def _serialize(review: SiteReview, session: AsyncSession) -> dict:
    user_row = await session.execute(select(User).where(User.id == review.user_id))
    user = user_row.scalar_one_or_none()
    return {
        "_id": review.id,
        "userId": review.user_id,
        "userName": user.name if user else "",
        "userEmail": user.email if user else "",
        "rating": review.rating,
        "comment": review.comment,
        "isApproved": review.is_approved,
        "createdAt": review.created_at.isoformat() if review.created_at else None,
    }


@router.post("", status_code=201)
async def create_site_review(
    payload: SiteReviewIn,
    claims: Annotated[dict, Depends(require_user)],
    session: Annotated[AsyncSession, Depends(_session)],
):
    review = SiteReview(
        user_id=claims["sub"],
        rating=payload.rating,
        comment=payload.comment,
        is_approved=False,
    )
    session.add(review)
    await session.commit()
    await session.refresh(review)
    return await _serialize(review, session)


@router.get("")
async def list_site_reviews(session: Annotated[AsyncSession, Depends(_session)]):
    rows = (
        await session.execute(
            select(SiteReview).where(SiteReview.is_approved.is_(True)).order_by(SiteReview.created_at.desc())
        )
    ).scalars().all()
    return {"reviews": [await _serialize(r, session) for r in rows]}


@router.get("/user")
async def list_user_site_reviews(
    claims: Annotated[dict, Depends(require_user)],
    session: Annotated[AsyncSession, Depends(_session)],
):
    rows = (
        await session.execute(select(SiteReview).where(SiteReview.user_id == claims["sub"]))
    ).scalars().all()
    return {"reviews": [await _serialize(r, session) for r in rows]}


@router.put("/status/{review_id}")
async def update_status(
    review_id: str,
    payload: StatusIn,
    _admin: Annotated[dict, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(_session)],
):
    res = await session.execute(select(SiteReview).where(SiteReview.id == review_id))
    review = res.scalar_one_or_none()
    if not review:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="site review not found")
    review.is_approved = payload.isApproved
    await session.commit()
    return await _serialize(review, session)


@router.put("/{review_id}")
async def update_site_review(
    review_id: str,
    payload: SiteReviewIn,
    claims: Annotated[dict, Depends(require_user)],
    session: Annotated[AsyncSession, Depends(_session)],
):
    res = await session.execute(select(SiteReview).where(SiteReview.id == review_id))
    review = res.scalar_one_or_none()
    if not review:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="site review not found")
    if claims.get("role") != "admin" and review.user_id != claims["sub"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="not your review")
    review.rating = payload.rating
    review.comment = payload.comment
    await session.commit()
    return await _serialize(review, session)


@router.delete("/{review_id}")
async def delete_site_review(
    review_id: str,
    claims: Annotated[dict, Depends(require_user)],
    session: Annotated[AsyncSession, Depends(_session)],
):
    res = await session.execute(select(SiteReview).where(SiteReview.id == review_id))
    review = res.scalar_one_or_none()
    if not review:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="site review not found")
    if claims.get("role") != "admin" and review.user_id != claims["sub"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="not your review")
    await session.delete(review)
    await session.commit()
    return {"message": "site review deleted"}
