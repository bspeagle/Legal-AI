"""
Legal AI: Virtual Courtroom Simulation
Main application entry point
"""
import os
import uvicorn
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time
from dotenv import load_dotenv
from src.api.router import api_router
from src.database.connection import create_db_and_tables
from src.utils.logging_config import setup_logging

# Setup logging
logger = setup_logging()

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="Legal AI Virtual Courtroom",
    description="An AI-powered virtual courtroom simulation platform",
    version="0.1.0"
)

# Include API routes
app.include_router(api_router)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    await create_db_and_tables()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Legal AI Virtual Courtroom API", 
        "status": "online",
        "version": "0.1.0"
    }

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
