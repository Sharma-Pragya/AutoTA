"""Authentication and name verification endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class VerifyNameRequest(BaseModel):
    student_id: str
    name: str


class VerifyNameResponse(BaseModel):
    verified: bool
    student_name: str | None = None
    student_id: str | None = None
    error: str | None = None


@router.post("/verify-name", response_model=VerifyNameResponse)
async def verify_name(request: VerifyNameRequest):
    """Verify student identity by checking name against database."""
    from autota.web.db import get_db_connection

    conn = get_db_connection()
    cursor = conn.cursor()

    # Look up student by ID
    cursor.execute(
        "SELECT id, name FROM students WHERE id = ?",
        (request.student_id,)
    )
    result = cursor.fetchone()
    conn.close()

    if not result:
        return VerifyNameResponse(
            verified=False,
            error="Student ID not found in our records."
        )

    db_id, db_name = result

    # Case-insensitive name comparison
    if request.name.strip().lower() == db_name.strip().lower():
        return VerifyNameResponse(
            verified=True,
            student_name=db_name,
            student_id=db_id
        )
    else:
        return VerifyNameResponse(
            verified=False,
            error="Name does not match our records for this assignment."
        )
