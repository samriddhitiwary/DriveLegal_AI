from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routes.chat import router as chat_router
from app.utils.logger import logger

app = FastAPI(
    title="DriveLegal AI Backend",
    description="Conversational RAG Chatbot for Traffic Laws and Regulations",
    version="1.0.0"
)

# Configure CORS Middleware for web/mobile client integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler to capture all unhandled server errors and log them
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."}
    )

app.include_router(chat_router)

@app.get("/")
async def root():
    logger.info("Root endpoint hit")
    return {"message": "DriveLegal AI Backend Running"}