#!/usr/bin/env python3
"""
Ollama LLM Integration for Dynamic Script Generation
Replaces hardcoded story templates with AI-generated content
"""
import os
import json
import yaml
from typing import Dict, List, Optional, Any
import ollama

class OllamaClient:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.ollama_config = self.config.get("ollama", {})
        self.base_url = self.ollama_config.get("base_url", os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
        self.model = self.ollama_config.get("model", os.getenv("OLLAMA_MODEL", "llama3.1:8b"))
        self.timeout = self.ollama_config.get("timeout", int(os.getenv("OLLAMA_TIMEOUT", "120")))

        # Initialize ollama client
        self.client = ollama.Client(host=self.base_url, timeout=self.timeout)

    def _load_config(self, path: str) -> dict:
        with open(path) as f:
            return yaml.safe_load(f)

    def list_models(self) -> List[str]:
        """Get available Ollama models"""
        try:
            models = self.client.list()
            return [m['name'] for m in models.get('models', [])]
        except Exception as e:
            print(f"⚠️ Failed to list Ollama models: {e}")
            return [self.model]

    def is_available(self) -> bool:
        """Check if Ollama is running and model is available"""
        try:
            models = self.list_models()
            return self.model in models or len(models) > 0
        except Exception:
            return False

    def generate(self, prompt: str, system: str = None, temperature: float = 0.7) -> str:
        """Generate text using Ollama"""
        try:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            response = self.client.chat(
                model=self.model,
                messages=messages,
                options={"temperature": temperature}
            )
            return response['message']['content'].strip()
        except Exception as e:
            print(f"❌ Ollama generation failed: {e}")
            return ""

    def generate_json(self, prompt: str, system: str = None, temperature: float = 0.3) -> dict:
        """Generate structured JSON response"""
        json_prompt = prompt + "\n\nRespond ONLY with valid JSON. No extra text."
        response = self.generate(json_prompt, system, temperature)
        try:
            # Extract JSON from response
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except Exception as e:
            print(f"❌ Failed to parse JSON: {e}")
        return {}


class ScriptGenerator:
    """Generates video scripts using Ollama LLM"""

    def __init__(self, ollama_client: OllamaClient, config: dict):
        self.ollama = ollama_client
        self.config = config
        self.characters = config.get("characters", {})

    def generate_short_script(self, week: int, day: int, theme: str = None) -> dict:
        """Generate a single short script"""
        char_names = list(self.characters.keys())
        main_char = char_names[day % len(char_names)]
        char_config = self.characters[main_char]

        system = f"""You are a children's cartoon writer for "Toonora" channel.
Create funny, educational 20-second shorts for kids aged 4-8.
Characters: {', '.join([f'{name} ({cfg["personality"]})' for name, cfg in self.characters.items()])}
Main character for this short: {main_char} - {char_config['personality']}
Style: Funny, simple dialogue, visual comedy, positive messages."""

        prompt = f"""Generate a 20-second cartoon short script for Week {week}, Day {day+1}.
Theme: {theme or 'Daily adventure'}
Main character: {main_char}

Return JSON with:
{{
  "title": "Short title",
  "main_char": "{main_char}",
  "scenes": [
    {{"action": "description", "dialogue": "character speech", "duration": 3, "bg": "room/park/kitchen/bedroom"}},
    ...
  ]
}}

3-4 scenes max. Each scene 3-5 seconds. Total ~20 seconds.
Dialogue should be 1-2 short sentences per scene."""

        script = self.ollama.generate_json(prompt, system)

        # Add metadata
        script.setdefault("type", "short")
        script.setdefault("day", day)
        script.setdefault("week", week)
        script.setdefault("main_char", main_char)

        return script

    def generate_episode_script(self, week: int, theme: str = None) -> dict:
        """Generate a weekly episode script with all characters"""
        char_names = list(self.characters.keys())

        system = f"""You are a children's cartoon writer for "Toonora" channel.
Create a 2-minute episode featuring ALL characters together.
Characters: {', '.join([f'{name} ({cfg["personality"]})' for name, cfg in self.characters.items()])}
Style: Funny, heartwarming, teamwork, simple dialogue."""

        prompt = f"""Generate a 2-minute cartoon episode script for Week {week}.
Theme: {theme or 'Weekly adventure'}
All characters: {', '.join(char_names)}

Return JSON with:
{{
  "title": "Episode title",
  "chars": {char_names},
  "scenes": [
    {{"action": "description", "chars": ["char1", "char2"], "dialogue": ["speech1", "speech2"], "duration": 8, "bg": "room/park/kitchen/bedroom"}},
    ...
  ]
}}

5-6 scenes max. Each scene 8-15 seconds. Total ~120 seconds.
Each scene: multiple characters interact. Dialogue array matches chars array."""

        script = self.ollama.generate_json(prompt, system)
        script.setdefault("type", "episode")
        script.setdefault("week", week)
        return script

    def generate_weekly_content(self, week: int) -> dict:
        """Generate full week: 5 shorts + 1 episode"""
        print(f"🤖 Generating Week {week} content with Ollama ({self.ollama.model})...")

        shorts = []
        themes = ["discovery", "friendship", "learning", "creativity", "kindness"]

        for day in range(5):
            theme = themes[day] if day < len(themes) else "adventure"
            short = self.generate_short_script(week, day, theme)
            shorts.append(short)
            print(f"  ✅ Short {day+1}: {short.get('title', 'Untitled')}")

        episode = self.generate_episode_script(week, "weekly adventure")
        print(f"  ✅ Episode: {episode.get('title', 'Untitled')}")

        return {
            "week": week,
            "generated_at": self._now_iso(),
            "shorts": shorts,
            "episode": episode
        }

    def _now_iso(self) -> str:
        from datetime import datetime
        return datetime.now().isoformat()


class MetadataGenerator:
    """Generates YouTube metadata (title, description, tags)"""

    def __init__(self, ollama_client: OllamaClient, config: dict):
        self.ollama = ollama_client
        self.config = config
        self.channel_name = config.get("channel", {}).get("name", "Toonora")

    def generate_short_metadata(self, script: dict) -> dict:
        """Generate metadata for a short"""
        system = f"""You are a YouTube SEO expert for kids' channel "{self.channel_name}".
Create engaging, kid-friendly titles and descriptions that parents trust."""

        prompt = f"""Generate YouTube metadata for this short:
Title: {script.get('title', '')}
Character: {script.get('main_char', '')}
Scenes: {len(script.get('scenes', []))}

Return JSON:
{{
  "title": "Engaging title under 60 chars with emoji",
  "description": "Kid-friendly description with hashtags",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "hashtags": ["#shorts", "#cartoons", "#kids"]
}}"""

        return self.ollama.generate_json(prompt, system)

    def generate_episode_metadata(self, script: dict) -> dict:
        """Generate metadata for an episode"""
        system = f"""You are a YouTube SEO expert for kids' channel "{self.channel_name}".
Create engaging titles and descriptions for 2-minute episodes."""

        prompt = f"""Generate YouTube metadata for this episode:
Title: {script.get('title', '')}
Characters: {', '.join(script.get('chars', []))}
Scenes: {len(script.get('scenes', []))}

Return JSON:
{{
  "title": "Engaging title under 60 chars with emoji",
  "description": "Kid-friendly description with subscribe call-to-action",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6"],
  "hashtags": ["#cartoons", "#kids", "#animation"]
}}"""

        return self.ollama.generate_json(prompt, system)


if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--week", type=int, default=1)
    parser.add_argument("--list-models", action="store_true")
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    ollama_client = OllamaClient()

    if args.list_models:
        models = ollama_client.list_models()
        print("Available models:", models)
        sys.exit(0)

    if not ollama_client.is_available():
        print(f"❌ Ollama not available at {ollama_client.base_url}")
        print(f"   Make sure Ollama is running and model '{ollama_client.model}' is pulled")
        sys.exit(1)

    print(f"✅ Ollama available: {ollama_client.model}")

    config = ollama_client.config
    generator = ScriptGenerator(ollama_client, config)

    if args.test:
        # Quick test
        short = generator.generate_short_script(1, 0, "test")
        print("Test short:", json.dumps(short, indent=2))
    else:
        # Full week
        content = generator.generate_weekly_content(args.week)

        # Save scripts
        import os
        from pathlib import Path
        output_dir = Path(config["paths"]["output"]) / f"week_{args.week}"
        output_dir.mkdir(parents=True, exist_ok=True)

        script_file = output_dir / "scripts.json"
        with open(script_file, "w") as f:
            json.dump(content, f, indent=2)

        print(f"\n✅ Saved to {script_file}")
        print(f"   Shorts: {len(content['shorts'])}")
        print(f"   Episode: {content['episode'].get('title', 'N/A')}")