#!/usr/bin/env python3
"""
FastAPI Server for Toonora Pipeline (MoneyPrinter style)
Provides web UI endpoints for generating and managing content
"""
import os
import json
import yaml
import subprocess
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Load config
CONFIG_PATH = os.getenv("CONFIG_PATH", "config.yaml")
with open(CONFIG_PATH) as f:
    CONFIG = yaml.safe_load(f)

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://toonora:toonora123@postgres:5432/toonora")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Models
class JobStatus(str):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class JobType(str):
    GENERATE_SCRIPTS = "generate_scripts"
    GENERATE_AUDIO = "generate_audio"
    RENDER_VIDEO = "render_video"
    UPLOAD_YOUTUBE = "upload_youtube"
    FULL_PIPELINE = "full_pipeline"

class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(SQLEnum(JobType), nullable=False)
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING)
    week = Column(Integer, nullable=False)
    params = Column(Text)  # JSON
    result = Column(Text)  # JSON
    error = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(
    title="Toonora Pipeline API",
    description="MoneyPrinter-style API for automated cartoon generation",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class GenerateRequest(BaseModel):
    week: int = Field(..., ge=1, le=52)
    use_ai: bool = True
    use_stock: bool = True
    upload: bool = False

class JobResponse(BaseModel):
    job_id: str
    status: str
    message: str

# Ollama check
def check_ollama():
    import requests
    try:
        r = requests.get("http://ollama:11434/api/tags", timeout=5)
        return r.status_code == 200
    except:
        return False

# Background task
def run_pipeline_task(job_id: str, week: int, use_ai: bool, use_stock: bool, upload: bool):
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return

        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        db.commit()

        # Import and run pipeline
        from enhanced_pipeline import EnhancedPipeline
        pipeline = EnhancedPipeline()

        success = pipeline.run_week(week, use_ai=use_ai, use_stock=use_stock)

        if success and upload:
            pipeline.upload_week(week)

        job.status = JobStatus.COMPLETED if success else JobStatus.FAILED
        job.result = json.dumps({"week": week, "success": success})
        if not success:
            job.error = "Pipeline failed - check logs"

    except Exception as e:
        job.status = JobStatus.FAILED
        job.error = str(e)
    finally:
        job.completed_at = datetime.utcnow()
        db.commit()
        db.close()

# API Endpoints
@app.get("/")
def root():
    return {
        "name": "Toonora Pipeline API",
        "version": "2.0.0",
        "style": "MoneyPrinter",
        "ollama_available": check_ollama()
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "ollama": check_ollama(),
        "database": "connected"
    }

@app.post("/generate", response_model=JobResponse)
def generate_content(request: GenerateRequest, background_tasks: BackgroundTasks):
    """Start a new content generation job"""
    db = SessionLocal()
    try:
        job = Job(
            type=JobType.FULL_PIPELINE,
            week=request.week,
            params=json.dumps({
                "use_ai": request.use_ai,
                "use_stock": request.use_stock,
                "upload": request.upload
            })
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        background_tasks.add_task(
            run_pipeline_task,
            job.id, request.week,
            request.use_ai, request.use_stock, request.upload
        )

        return JobResponse(
            job_id=job.id,
            status=job.status,
            message=f"Started pipeline for week {request.week}"
        )
    finally:
        db.close()

@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    """Get job status"""
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(404, "Job not found")
        return {
            "id": job.id,
            "type": job.type,
            "status": job.status,
            "week": job.week,
            "params": json.loads(job.params) if job.params else {},
            "result": json.loads(job.result) if job.result else {},
            "error": job.error,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        }
    finally:
        db.close()

@app.get("/jobs")
def list_jobs(limit: int = 50, status: Optional[str] = None):
    """List recent jobs"""
    db = SessionLocal()
    try:
        query = db.query(Job).order_by(Job.created_at.desc())
        if status:
            query = query.filter(Job.status == status)
        jobs = query.limit(limit).all()
        return [{
            "id": j.id,
            "type": j.type,
            "status": j.status,
            "week": j.week,
            "created_at": j.created_at.isoformat() if j.created_at else None,
        } for j in jobs]
    finally:
        db.close()

@app.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: str):
    """Cancel a pending/running job"""
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(404, "Job not found")
        if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            raise HTTPException(400, "Job cannot be cancelled")
        job.status = JobStatus.CANCELLED
        db.commit()
        return {"message": "Job cancelled", "job_id": job_id}
    finally:
        db.close()

@app.get("/ollama/models")
def list_ollama_models():
    """List available Ollama models"""
    import requests
    try:
        r = requests.get("http://ollama:11434/api/tags", timeout=5)
        return r.json()
    except Exception as e:
        raise HTTPException(503, f"Ollama unavailable: {e}")

@app.post("/scripts/generate")
def generate_scripts(week: int):
    """Generate scripts for a week using Ollama"""
    from ollama_client import OllamaClient, ScriptGenerator
    ollama = OllamaClient()
    if not ollama.is_available():
        raise HTTPException(503, "Ollama not available")
    generator = ScriptGenerator(ollama, CONFIG)
    content = generator.generate_weekly_content(week)

    # Save
    output_dir = Path(CONFIG["paths"]["output"]) / f"week_{week}"
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "scripts.json", "w") as f:
        json.dump(content, f, indent=2)

    return {"message": f"Generated week {week} scripts", "shorts": len(content["shorts"]), "episode": content["episode"].get("title")}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)