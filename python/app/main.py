"""
FastAPI Main Application.
Intelligent Scam Detection System - Python AI Server
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import SERVER_HOST, SERVER_PORT
from app.models import AnalyzeRequest, AnalyzeResponse
from app.services.analyzer import analyze_url
from app.services.whitelist import load_whitelist

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Loads whitelist on startup.
    """
    logger.info("Starting AI Analysis Server...")
    
    # Load whitelist into memory
    whitelist = load_whitelist()
    logger.info(f"Whitelist loaded with {len(whitelist)} domains")
    
    yield
    
    logger.info("Shutting down AI Analysis Server...")


# Create FastAPI application
app = FastAPI(
    title="Intelligent Scam Detection API",
    description="AI-powered URL analysis for phishing and scam detection",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Intelligent Scam Detection API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "components": {
            "api": "up",
            "whitelist": "loaded"
        }
    }


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    """
    Analyze a URL for potential scam/phishing risks.
    
    Executes a 5-phase analysis pipeline:
    - Phase 0: Whitelist filtering
    - Phase 1: Redirect tracking
    - Phase 2: Domain metadata analysis
    - Phase 3: AI semantic analysis (Claude Haiku 4.5)
    - Phase 4: Search engine cross-verification
    
    Returns risk score and status (SAFE/WARNING/BLOCK).
    """
    try:
        logger.info(f"Received analysis request: {request.request_id}")
        
        result = await analyze_url(request)
        
        logger.info(f"Analysis complete: {request.request_id} -> {result.status}")
        
        return result
        
    except Exception as e:
        logger.error(f"Analysis failed for {request.request_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        reload=True
    )
