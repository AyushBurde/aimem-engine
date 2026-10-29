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
    import os
    os.makedirs("data", exist_ok=True)
    create_tables()
    yield


app = FastAPI(
    title="aimem",
    description="AI Agent Memory Service — context-aware memory for AI apps",
    version="0.1.0",
    lifespan=lifespan,
)

# Allow Next.js frontend (port 3000 / Vercel) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi import Request
from aimem.config import (
    current_provider,
    current_gemini_key,
    current_openai_key,
    current_openrouter_key,
)

@app.middleware("http")
async def capture_request_api_keys(request: Request, call_next):
    prov = request.headers.get("x-provider")
    gemini_k = request.headers.get("x-gemini-api-key")
    openai_k = request.headers.get("x-openai-api-key")
    openrouter_k = request.headers.get("x-openrouter-api-key")
    raw_k = request.headers.get("x-api-key")

    if raw_k and not (gemini_k or openai_k or openrouter_k):
        if raw_k.startswith("AIza"):
            gemini_k = raw_k
            prov = prov or "gemini"
        elif raw_k.startswith("sk-or-"):
            openrouter_k = raw_k
            openai_k = raw_k
            prov = prov or "openrouter"
        elif raw_k.startswith("sk-"):
            openai_k = raw_k
            prov = prov or "openai"
        else:
            if prov == "openai":
                openai_k = raw_k
            elif prov == "openrouter":
                openrouter_k = raw_k
                openai_k = raw_k
            else:
                gemini_k = raw_k
                prov = prov or "gemini"

    token_p = current_provider.set(prov)
    token_g = current_gemini_key.set(gemini_k)
    token_o = current_openai_key.set(openai_k)
    token_r = current_openrouter_key.set(openrouter_k)

    try:
        response = await call_next(request)
        return response
    finally:
        current_provider.reset(token_p)
        current_gemini_key.reset(token_g)
        current_openai_key.reset(token_o)
        current_openrouter_key.reset(token_r)

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
