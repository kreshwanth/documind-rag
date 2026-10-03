from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.database import init_db
from app.api.v1 import health, auth, documents, chat, search, conversations, dashboard
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("documind.main")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Enterprise Document Management & Retrieval-Augmented Generation (RAG) Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting DocuMind Engine...")
    init_db()
    logger.info("DocuMind database and vector extensions initialized.")

# Global generic error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred."}
    )

# Direct Route Bindings (/api/...)
app.include_router(health.router, tags=["Health"])
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(chat.router, prefix="/api/chat", tags=["RAG Chat"])
app.include_router(search.router, prefix="/api/search", tags=["Semantic Search"])
app.include_router(conversations.router, prefix="/api/conversations", tags=["Conversations"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard & Analytics"])

# Versioned Aliases (/api/v1/...)
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["RAG Chat"])
app.include_router(search.router, prefix="/api/v1/search", tags=["Semantic Search"])
app.include_router(conversations.router, prefix="/api/v1/conversations", tags=["Conversations"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard & Analytics"])

@app.get("/")
def root_endpoint():
    return {
        "name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "status": "operational",
        "health": "/health",
        "docs": "/docs"
    }
