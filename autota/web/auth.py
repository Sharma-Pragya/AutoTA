"""Simple token-based auth for instructor endpoints.

The token is read from the AUTOTA_INSTRUCTOR_TOKEN environment variable.
If the env var is unset, auth is disabled (dev mode — logs a warning on startup).

Usage:
    from autota.web.auth import require_instructor
    from fastapi import Depends

    @router.get("/something")
    async def my_endpoint(_: None = Depends(require_instructor)):
        ...
"""

import os
import logging
from fastapi import Header, HTTPException

logger = logging.getLogger(__name__)

_TOKEN = os.environ.get("AUTOTA_INSTRUCTOR_TOKEN", "").strip()

if not _TOKEN:
    logger.warning(
        "AUTOTA_INSTRUCTOR_TOKEN is not set — instructor endpoints are unprotected. "
        "Set this env var before deploying."
    )


async def require_instructor(x_instructor_token: str = Header(default="")):
    """FastAPI dependency: validates the X-Instructor-Token header.

    Pass via header:  X-Instructor-Token: <token>
    Or skip entirely in dev mode (when AUTOTA_INSTRUCTOR_TOKEN is unset).
    """
    if not _TOKEN:
        # Dev mode: no token configured, allow all
        return
    if x_instructor_token != _TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing instructor token")
