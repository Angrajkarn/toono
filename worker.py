#!/usr/bin/env python3
"""
Background Worker for Toonora Pipeline (MoneyPrinter style)
Processes jobs from the database queue
"""
import os
import json
import time
import signal
import sys
import yaml
import subprocess
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Load config
CONFIG_PATH = os.getenv("CONFIG_PATH", "config.yaml")
with open(CONFIG_PATH) as f:
    CONFIG = yaml.safe_load(f)

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://toonora:toonora123@postgres:5432/toonora")

# Import models from api
sys.path.append(os.path.dirname(__file__))
from api import engine, SessionLocal, Job, JobStatus, JobType

# Graceful shutdown
shutdown = False

def signal_handler(signum, frame):
    global shutdown
    print("\n🛑 Shutdown signal received...")
    shutdown = True

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


def process_job(job):
    """Process a single job"""
    db = SessionLocal()
    try:
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        db.commit()

        params = json.loads(job.params) if job.params else {}
        week = job.week
        use_ai = params.get("use_ai", True)
        use_stock = params.get("use_stock", True)
        upload = params.get("upload", False)

        print(f"🎬 Processing job {job.id} - Week {week} ({job.type})")

        # Import pipeline
        from enhanced_pipeline import EnhancedPipeline
        pipeline = EnhancedPipeline()

        success = False
        error = None

        try:
            if job.type == "generate_scripts":
                from ollama_client import OllamaClient, ScriptGenerator
                ollama = OllamaClient()
                if not ollama.is_available():
                    raise Exception("Ollama not available")
                generator = ScriptGenerator(ollama, CONFIG)
                content = generator.generate_weekly_content(week)

                # Save
                output_dir = Path(CONFIG["paths"]["output"]) / f"week_{week}"
                output_dir.mkdir(parents=True, exist_ok=True)
                with open(output_dir / "scripts.json", "w") as f:
                    json.dump(content, f, indent=2)

                success = True

            elif job.type == "generate_audio":
                result = subprocess.run([
                    sys.executable, "generate_audio.py", f"--week={week}"
                ], capture_output=True, text=True, timeout=300)
                success = result.returncode == 0

            elif job.type == "render_video":
                result = subprocess.run([
                    sys.executable, "animate.py", f"--week={week}"
                ], capture_output=True, text=True, timeout=7200)
                success = result.returncode == 0

            elif job.type == "upload_youtube":
                result = subprocess.run([
                    sys.executable, "upload.py", f"--week={week}"
                ], capture_output=True, text=True, timeout=3600)
                success = result.returncode == 0

            elif job.type == "full_pipeline":
                from enhanced_pipeline import EnhancedPipeline
                pipeline = EnhancedPipeline()
                success = pipeline.run_week(week, use_ai=True, use_stock=True)
                if success:
                    upload_param = json.loads(job.params).get("upload", False)
                    if upload_param:
                        pipeline.upload_week(week)

        except Exception as e:
            error = str(e)
            print(f"❌ Job {job.id} failed: {error}")

        # Update job status
        job.status = JobStatus.COMPLETED if success else JobStatus.FAILED
        job.result = json.dumps({"success": success, "week": week})
        if error:
            job.error = error
        job.completed_at = datetime.utcnow()
        db.commit()

        print(f"{'✅' if success else '❌'} Job {job.id} {'completed' if success else 'failed'}")

    except Exception as e:
        print(f"❌ Worker error: {e}")
        job.status = JobStatus.FAILED
        job.error = str(e)
        job.completed_at = datetime.utcnow()
        db.commit()
    finally:
        db.close()


def main():
    print("🔧 Toonora Worker Starting...")
    print(f"   Database: {DATABASE_URL}")
    print(f"   Polling interval: 10s")
    print(f"   Press Ctrl+C to stop")

    while not shutdown:
        db = SessionLocal()
        try:
            # Find pending jobs
            pending_jobs = db.query(Job).filter(
                Job.status == JobStatus.PENDING
            ).order_by(Job.created_at).limit(5).all()

            for job in pending_jobs:
                if shutdown:
                    break
                process_job(job)

        except Exception as e:
            print(f"❌ Worker loop error: {e}")
        finally:
            db.close()

        if shutdown:
            break

        # Wait before next poll
        for _ in range(10):
            if shutdown:
                break
            time.sleep(1)

    print("👋 Worker stopped")


if __name__ == "__main__":
    import time
    main()