#!/usr/bin/env python3
"""
Enhanced Pipeline - Integrates Ollama LLM + Pexels Stock Videos + Improved Rendering
Replaces hardcoded templates with AI-generated content and real stock footage
"""
import os
import sys
import json
import yaml
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Import our modules
from ollama_client import OllamaClient, ScriptGenerator, MetadataGenerator
from pexels_client import VideoAssetManager
from animate import render_week as render_week_original
from generate_audio import main as generate_audio_main
from upload import main as upload_main


class EnhancedPipeline:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.ollama = OllamaClient(config_path)
        self.script_gen = ScriptGenerator(self.ollama, self.config)
        self.meta_gen = MetadataGenerator(self.ollama, self.config)
        self.video_assets = VideoAssetManager(self.config)

    def _load_config(self, path: str) -> dict:
        with open(path) as f:
            return yaml.safe_load(f)

    def run_week(self, week: int, use_ai: bool = True, use_stock: bool = True) -> bool:
        """Run complete pipeline for a week"""
        print(f"\n{'='*60}")
        print(f"🎬 ENHANCED PIPELINE - WEEK {week}")
        print(f"{'='*60}")

        scripts_file = Path(self.config["paths"]["output"]) / f"week_{week}" / "scripts.json"

        # Step 1: Generate or load scripts
        if use_ai and self.ollama.is_available():
            print("🤖 Generating scripts with Ollama...")
            content = self.script_gen.generate_weekly_content(week)
            scripts_file.parent.mkdir(parents=True, exist_ok=True)
            with open(scripts_file, "w") as f:
                json.dump(content, f, indent=2)
            print(f"✅ Scripts saved to {scripts_file}")
        else:
            if not scripts_file.exists():
                print(f"❌ Scripts not found: {scripts_file}")
                print("   Run with --use-ai or generate scripts first")
                return False
            print(f"📄 Loading existing scripts from {scripts_file}")

        # Step 2: Download stock videos (optional)
        if use_stock and self.video_assets.pexels.is_configured():
            print("📥 Fetching stock videos from Pexels...")
            with open(scripts_file) as f:
                content = json.load(f)
            videos = self.video_assets.get_videos_for_week(content)
            print(f"✅ Downloaded {len(videos)} stock videos")
        else:
            if use_stock:
                print("⚠️ Pexels not configured, using SVG backgrounds")

        # Step 3: Generate audio
        print("🎙️ Generating voiceovers...")
        try:
            # Call existing generate_audio.py
            result = subprocess.run([
                sys.executable, "generate_audio.py", f"--week={week}"
            ], capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                print(f"❌ Audio generation failed: {result.stderr}")
                return False
            print("✅ Audio generated")
        except subprocess.TimeoutExpired:
            print("❌ Audio generation timed out")
            return False
        except Exception as e:
            print(f"❌ Audio generation error: {e}")
            return False

        # Step 4: Render videos
        print("🎬 Rendering videos...")
        try:
            result = subprocess.run([
                sys.executable, "animate.py", f"--week={week}"
            ], capture_output=True, text=True, timeout=7200)
            if result.returncode != 0:
                print(f"❌ Video rendering failed: {result.stderr[:2000]}")
                return False
            print("✅ Videos rendered")
        except subprocess.TimeoutExpired:
            print("❌ Video rendering timed out")
            return False
        except Exception as e:
            print(f"❌ Video rendering error: {e}")
            return False

        # Step 5: Generate metadata (optional)
        if use_ai and self.ollama.is_available():
            print("📝 Generating YouTube metadata...")
            self._generate_metadata(week)

        print(f"\n{'='*60}")
        print(f"🎉 WEEK {week} COMPLETE!")
        print(f"{'='*60}")
        return True

    def _generate_metadata(self, week: int):
        """Generate YouTube metadata for all videos"""
        scripts_file = Path(self.config["paths"]["output"]) / f"week_{week}" / "scripts.json"
        with open(scripts_file) as f:
            content = json.load(f)

        metadata = {"week": week, "shorts": [], "episode": {}}

        # Shorts metadata
        for short in content.get("shorts", []):
            meta = self.meta_gen.generate_short_metadata(short)
            metadata["shorts"].append(meta)

        # Episode metadata
        metadata["episode"] = self.meta_gen.generate_episode_metadata(content.get("episode", {}))

        # Save metadata
        meta_file = Path(self.config["paths"]["output"]) / f"week_{week}" / "metadata.json"
        with open(meta_file, "w") as f:
            json.dump(metadata, f, indent=2)

        print(f"✅ Metadata saved to {meta_file}")

    def upload_week(self, week: int) -> bool:
        """Upload to YouTube"""
        print("📤 Uploading to YouTube...")
        try:
            result = subprocess.run([
                sys.executable, "upload.py", f"--week={week}"
            ], capture_output=True, text=True, timeout=3600)
            if result.returncode != 0:
                print(f"❌ Upload failed: {result.stderr}")
                return False
            print("✅ Upload complete")
            return True
        except subprocess.TimeoutExpired:
            print("❌ Upload timed out")
            return False
        except Exception as e:
            print(f"❌ Upload error: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description="Enhanced Cartoon Pipeline with AI")
    parser.add_argument("--week", type=int, required=True, help="Week number")
    parser.add_argument("--no-ai", action="store_true", help="Disable AI script generation")
    parser.add_argument("--no-stock", action="store_true", help="Disable Pexels stock videos")
    parser.add_argument("--no-upload", action="store_true", help="Skip YouTube upload")
    parser.add_argument("--metadata-only", action="store_true", help="Only generate metadata")
    args = parser.parse_args()

    pipeline = EnhancedPipeline()

    if args.metadata_only:
        pipeline._generate_metadata(args.week)
        return

    success = pipeline.run_week(
        args.week,
        use_ai=not args.no_ai,
        use_stock=not args.no_stock
    )

    if success and not args.no_upload:
        pipeline.upload_week(args.week)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()