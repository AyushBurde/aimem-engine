"""
aimem server — run with:  uvicorn main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from aimem.api.routes import router
from aimem.db.database import create_tables
from aimem.api.auth import auth_router



@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    create_tables()
    yield


app = FastAPI(
    title="aimem",
    description="AI Agent Memory Service — context-aware memory for AI apps",
    version="0.1.0",
    lifespan=lifespan,
)

# Allow Next.js frontend (port 3000) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routes
app.include_router(router)
app.include_router(auth_router)



@app.get("/")
def root():
    return {"service": "aimem", "status": "running", "version": "0.1.0"}


if __name__ == "__main__":
    import os
    import uvicorn
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host=host, port=port, reload=False)
