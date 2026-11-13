#!/usr/bin/env python3
"""
🎬 MASTER PIPELINE - Runs EVERYTHING automatically
===================================================
This is the ONLY command you ever need to run!

Usage:
  python run_pipeline.py                    # Run current week (auto-detects)
  python run_pipeline.py --week 1           # Run specific week
  python run_pipeline.py --all              # Run all weeks 1-52
  python run_pipeline.py --setup            # First-time setup (assets + auth)
  python run_pipeline.py --schedule         # Run as daemon (checks daily)

FULLY AUTOMATED - No manual steps after setup!
"""
import sys
import os
import yaml
import subprocess
import time
from pathlib import Path
from datetime import datetime, timedelta

def load_config():
    with open("config.yaml") as f:
        return yaml.safe_load(f)

def run_command(cmd, description, cwd=None):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"   Command: {' '.join(cmd)}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=3600)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"⚠️  stderr: {result.stderr}")
        if result.returncode != 0:
            print(f"❌ FAILED (exit code: {result.returncode})")
            return False
        print(f"✅ {description} - SUCCESS")
        return True
    except subprocess.TimeoutExpired:
        print(f"❌ TIMEOUT: {description}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def get_current_week(config):
    """Auto-detect current week based on start date"""
    # Default: start from first run, or you can set a start date in config
    start_date_str = config.get("automation", {}).get("start_date")
    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    else:
        # Use first Monday of current year as default
        now = datetime.now()
        start_date = datetime(now.year, 1, 1)
        while start_date.weekday() != 0:  # Monday
            start_date += timedelta(days=1)

    now = datetime.now()
    week_num = ((now - start_date).days // 7) + 1
    return max(1, min(week_num, 52))

def setup_first_time(config):
    """Run first-time setup: generate assets + authorize YouTube"""
    print("\n🚀 FIRST-TIME SETUP")
    print("="*60)

    # 1. Generate assets
    if not run_command(
        [sys.executable, "generate_assets.py"],
        "Generating character & background assets"
    ):
        return False

    # 2. Check for client_secret.json
    if not Path("client_secret.json").exists():
        print("\n⚠️  YouTube API setup needed:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create project → Enable 'YouTube Data API v3'")
        print("3. Create OAuth 2.0 credentials (Desktop app)")
        print("4. Download as 'client_secret.json' → place in this folder")
        print("\nThen run: python run_pipeline.py --setup")
        return False

    # 3. Authorize YouTube
    if not run_command(
        [sys.executable, "upload.py", "--auth"],
        "Authorizing YouTube API (opens browser)"
    ):
        return False

    print("\n✅ SETUP COMPLETE!")
    print("Now run: python run_pipeline.py")
    return True

def run_full_pipeline(week_num, config):
    """Run complete pipeline for one week"""
    print(f"\n{'#'*60}")
    print(f"#  PIPELINE: WEEK {week_num}")
    print(f"#  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}")

    steps = [
        ([sys.executable, "generate_scripts.py", f"--week={week_num}"],
         f"Generating scripts for Week {week_num}"),
        ([sys.executable, "generate_audio.py", f"--week={week_num}"],
         f"Generating voiceovers for Week {week_num}"),
        ([sys.executable, "animate.py", f"--week={week_num}"],
         f"Rendering videos for Week {week_num}"),
        ([sys.executable, "upload.py", f"--week={week_num}"],
         f"Uploading to YouTube for Week {week_num}"),
    ]

    for cmd, desc in steps:
        if not run_command(cmd, desc):
            print(f"\n❌ PIPELINE FAILED at: {desc}")
            print(f"   Fix the issue and re-run: python run_pipeline.py --week {week_num}")
            return False

    # Cleanup old temp files
    cleanup_old_files(config)

    print(f"\n{'='*60}")
    print(f"🎉 WEEK {week_num} COMPLETE - FULLY AUTOMATED!")
    print(f"{'='*60}")
    return True

def cleanup_old_files(config):
    """Remove old render files to save space"""
    keep_days = config.get("automation", {}).get("keep_days", 30)
    cutoff = datetime.now() - timedelta(days=keep_days)

    for path_str in [config["paths"]["output"], config["paths"]["temp"]]:
        path = Path(path_str)
        if path.exists():
            for item in path.iterdir():
                try:
                    mtime = datetime.fromtimestamp(item.stat().st_mtime)
                    if mtime < cutoff:
                        if item.is_dir():
                            import shutil
                            shutil.rmtree(item)
                        else:
                            item.unlink()
                        print(f"🗑️  Cleaned: {item}")
                except:
                    pass

def run_scheduler(config):
    """Run as daemon - checks daily for new week"""
    print("⏰ SCHEDULER MODE - Checking daily for new content")
    print("Press Ctrl+C to stop")

    last_week = 0

    while True:
        try:
            current_week = get_current_week(config)

            if current_week != last_week:
                print(f"\n📅 New week detected: {current_week}")
                run_full_pipeline(current_week, config)
                last_week = current_week

            # Check every hour
            time.sleep(3600)

        except KeyboardInterrupt:
            print("\n👋 Scheduler stopped")
            break
        except Exception as e:
            print(f"⚠️ Scheduler error: {e}")
            time.sleep(300)  # Wait 5 min on error

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fully Automated Cartoon Channel Pipeline")
    parser.add_argument("--week", type=int, help="Specific week to process")
    parser.add_argument("--all", action="store_true", help="Process all weeks 1-52")
    parser.add_argument("--setup", action="store_true", help="First-time setup")
    parser.add_argument("--schedule", action="store_true", help="Run as daily scheduler daemon")
    parser.add_argument("--auto", action="store_true", help="Auto-detect current week (default)")
    args = parser.parse_args()

    config = load_config()

    # Create required directories
    for path_str in config["paths"].values():
        Path(path_str).mkdir(parents=True, exist_ok=True)

    if args.setup:
        setup_first_time(config)
        return

    if args.schedule:
        run_scheduler(config)
        return

    if args.all:
        print("🔄 Processing ALL weeks 1-52...")
        for week in range(1, 53):
            if not run_full_pipeline(week, config):
                print(f"⚠️ Week {week} failed, continuing...")
        return

    # Default: auto-detect current week
    week = args.week if args.week else get_current_week(config)
    print(f"📅 Auto-detected week: {week}")

    run_full_pipeline(week, config)

if __name__ == "__main__":
    main()