"""Product image upload to S3."""
from __future__ import annotations

import logging
import uuid
from typing import Annotated

import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from ..security import require_admin
from ..settings import settings

router = APIRouter()
logger = logging.getLogger(__name__)

_s3_client = None


def _get_s3_client():
    global _s3_client
    if _s3_client is None:
        region = settings.s3_images_region or settings.cognito_region
        _s3_client = boto3.client("s3", region_name=region)
    return _s3_client


ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/svg+xml",
}
MAX_FILE_SIZE = 5 * 1024 * 1024


@router.post("/upload")
async def upload_image(
    file: UploadFile,
    _admin: Annotated[dict, Depends(require_admin)],
):
    if not settings.s3_images_bucket:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Image storage not configured",
        )

    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {content_type}",
        )

    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="File too large (max 5 MB)",
        )

    ext = content_type.split("/")[-1]
    if ext == "svg+xml":
        ext = "svg"
    elif ext == "jpeg":
        ext = "jpg"
    key = f"products/{uuid.uuid4().hex}.{ext}"
    region = settings.s3_images_region or settings.cognito_region

    try:
        _get_s3_client().put_object(
            Bucket=settings.s3_images_bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
    except ClientError as exc:
        logger.error("S3 upload failed: %s", exc)
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Image upload failed",
        ) from exc

    url = f"https://{settings.s3_images_bucket}.s3.{region}.amazonaws.com/{key}"
    return {"url": url, "key": key}
