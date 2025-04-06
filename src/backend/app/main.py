from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from dotenv import load_dotenv
import logging
from app.utils.ai_processor import AIProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="ML Paper Visualizer API",
    description="API for visualizing ML model development processes from research papers",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the AIProcessor singleton early
ai_processor = AIProcessor()
logger.info("AIProcessor singleton initialized")

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to ML Paper Visualizer API"}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Shutdown event handler
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down - cleaning up resources")
    # Close the AIProcessor client
    await ai_processor.close()
    logger.info("AIProcessor resources cleaned up")

# Import and include routers
from app.routers import papers, workflow, visualization
app.include_router(papers.router, prefix="/api/papers", tags=["papers"])
app.include_router(workflow.router, prefix="/api/workflow", tags=["workflow"])
app.include_router(visualization.router, prefix="/api/visualization", tags=["visualization"])

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
