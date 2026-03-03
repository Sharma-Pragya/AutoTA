"""FastAPI application for AutoTA web interface."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup: Initialize database
    from autota.web.db import init_db
    init_db()
    yield
    # Shutdown: cleanup if needed
    pass


app = FastAPI(
    title="AutoTA API",
    description="Backend API for AutoTA student assessment system",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"ok": True}


# Import and include routers
from autota.web.routes import auth, assignment, submit, retry, instructor

app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(assignment.router, prefix="/api", tags=["assignment"])
app.include_router(submit.router, prefix="/api", tags=["submit"])
app.include_router(retry.router)
app.include_router(instructor.router)
