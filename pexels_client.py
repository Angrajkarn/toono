#!/usr/bin/env python3
"""
Pexels Stock Video Integration
Fetches real footage for video backgrounds instead of SVG animations
"""
import os
import requests
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
import time

class PexelsClient:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.pexels_config = self.config.get("pexels", {})
        self.api_key = self.pexels_config.get("api_key", os.getenv("PEXELS_API_KEY"))
        self.base_url = "https://api.pexels.com/videos"
        self.headers = {"Authorization": self.api_key} if self.api_key else {}

    def _load_config(self, path: str) -> dict:
        import yaml
        with open(path) as f:
            return yaml.safe_load(f)

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def search_videos(self, query: str, per_page: int = 5, orientation: str = "portrait") -> List[Dict]:
        """Search for stock videos"""
        if not self.is_configured():
            print("⚠️ Pexels API key not configured")
            return []

        params = {
            "query": query,
            "per_page": per_page,
            "orientation": orientation,
            "size": "medium"
        }

        try:
            response = requests.get(
                f"{self.base_url}/search",
                headers=self.headers,
                params=params,
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get("videos", [])
            else:
                print(f"⚠️ Pexels search failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Pexels search error: {e}")
        return []

    def download_video(self, video_url: str, output_path: Path) -> bool:
        """Download video file"""
        try:
            response = requests.get(video_url, stream=True, timeout=30)
            if response.status_code == 200:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True
        except Exception as e:
            print(f"❌ Download failed: {e}")
        return False


class VideoAssetManager:
    """Manages video assets - downloads and caches stock footage"""

    def __init__(self, config: dict):
        self.config = config
        self.pexels = PexelsClient()
        self.cache_dir = Path(config["paths"]["assets"]) / "stock_videos"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Mapping of scene backgrounds to Pexels search terms
        self.bg_search_terms = {
            "room": ["cozy living room", "kids playroom", "colorful bedroom", "home interior"],
            "park": ["sunny park", "green playground", "children playing outside", "nature park"],
            "kitchen": ["modern kitchen cooking", "family kitchen", "baking kitchen", "bright kitchen"],
            "bedroom": ["cozy bedroom", "kids bedroom", "colorful bedroom", "morning bedroom"]
        }

    def get_video_for_scene(self, bg_name: str, duration: float, video_type: str = "short") -> Optional[Path]:
        """Get or download a video for a scene background"""
        search_terms = self.bg_search_terms.get(bg_name, [bg_name])

        # Try each search term until we get a video
        for term in search_terms:
            videos = self.pexels.search_videos(term, per_page=3)
            for video in videos:
                # Find a suitable video file
                for vf in video.get("video_files", []):
                    if vf.get("width", 0) >= 1080 and vf.get("height", 0) >= 1920:
                        url = vf["link"]
                        filename = f"{bg_name}_{video['id']}.mp4"
                        output_path = self.cache_dir / filename

                        if output_path.exists():
                            return output_path

                        print(f"  📥 Downloading {bg_name} video from Pexels...")
                        if self.pexels.download_video(url, output_path):
                            print(f"  ✅ Downloaded: {filename}")
                            return output_path

        print(f"  ⚠️ No Pexels video found for {bg_name}, using fallback")
        return None

    def get_videos_for_week(self, week_scripts: dict, video_type: str = "short") -> Dict[str, Path]:
        """Download all needed videos for a week's scripts"""
        videos = {}

        # Collect unique backgrounds needed
        backgrounds_needed = set()

        for short in week_scripts.get("shorts", []):
            for scene in short.get("scenes", []):
                backgrounds_needed.add(scene.get("bg", "room"))

        episode = week_scripts.get("episode", {})
        for scene in episode.get("scenes", []):
            backgrounds_needed.add(scene.get("bg", "room"))

        print(f"📥 Fetching stock videos for {len(backgrounds_needed)} backgrounds...")

        for bg in backgrounds_needed:
            video_path = self.get_video_for_scene(bg, 10)
            if video_path:
                videos[bg] = video_path

        return videos


if __name__ == "__main__":
    import yaml

    with open("config.yaml") as f:
        config = yaml.safe_load(f)

    manager = VideoAssetManager(config)

    if manager.pexels.is_configured():
        print("✅ Pexels configured")
        # Test search
        videos = manager.pexels.search_videos("cozy living room", per_page=2)
        print(f"Found {len(videos)} videos")
    else:
        print("⚠️ Pexels not configured. Add PEXELS_API_KEY to config.yaml")