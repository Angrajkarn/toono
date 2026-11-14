#!/usr/bin/env python3
"""
Generate ALL voiceovers automatically using FREE Edge TTS (Microsoft)
Run: python generate_audio.py --week 1
"""
import asyncio
import json
import sys
import yaml
import edge_tts
from pathlib import Path

def load_config():
    with open("config.yaml") as f:
        return yaml.safe_load(f)

# Voice mapping - all FREE Microsoft Edge voices
VOICES = {
    "bip": "en-US-GuyNeural",       # Energetic kid
    "gloop": "en-US-EricNeural",    # Goofy, deeper
    "pip": "en-GB-SoniaNeural",     # Smart, British female
    "zap": "en-US-JennyNeural",     # Fast, excitable female
    "snooze": "en-US-RogerNeural",  # Slow, sleepy male
}

# Voice customization per character
VOICE_SETTINGS = {
    "bip": {"rate": "+15%", "pitch": "+10Hz", "volume": "+0%"},
    "gloop": {"rate": "-5%", "pitch": "-20Hz", "volume": "+0%"},
    "pip": {"rate": "+0%", "pitch": "+5Hz", "volume": "+0%"},
    "zap": {"rate": "+25%", "pitch": "+15Hz", "volume": "+0%"},
    "snooze": {"rate": "-20%", "pitch": "-10Hz", "volume": "-10%"},
}

async def generate_voice(text, voice, settings, output_path):
    """Generate single voiceover using Edge TTS with validation"""
    import subprocess

    communicate = edge_tts.Communicate(
        text,
        voice,
        rate=settings["rate"],
        pitch=settings["pitch"],
        volume=settings["volume"]
    )
    await communicate.save(output_path)

    # Validate the generated file
    await validate_audio_file(output_path)


async def validate_audio_file(file_path, max_retries=3):
    """Validate audio file is playable by ffmpeg, retry if needed"""
    import subprocess
    import asyncio

    for attempt in range(max_retries):
        # Check file exists and has content
        if not Path(file_path).exists():
            raise Exception(f"File not created: {file_path}")

        file_size = Path(file_path).stat().st_size
        if file_size < 1000:  # Less than 1KB is likely corrupted
            raise Exception(f"File too small ({file_size} bytes): {file_path}")

        # Try to read with ffprobe
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", str(file_path)],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                duration = float(result.stdout.strip())
                if duration > 0:
                    return  # Valid audio file
        except Exception:
            pass

        if attempt < max_retries - 1:
            await asyncio.sleep(1)
            continue
        raise Exception(f"Audio file validation failed after {max_retries} attempts: {file_path}")

async def generate_all_audio(script_file, config):
    with open(script_file) as f:
        data = json.load(f)

    week_num = data["week"]
    audio_dir = Path(config["paths"]["output"]) / f"week_{week_num}" / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    print(f"🎙️ Generating audio for Week {week_num}...")

    # Generate shorts audio
    for short in data["shorts"]:
        main_char = short["main_char"]
        voice = VOICES[main_char]
        settings = VOICE_SETTINGS[main_char]

        for i, scene in enumerate(short["scenes"]):
            text = scene["dialogue"]
            out_file = audio_dir / f"short_{short['day']+1}_scene_{i}.mp3"

            if out_file.exists():
                print(f"  ⏭️  Exists: {out_file.name}")
                continue

            try:
                await generate_voice(text, voice, settings, str(out_file))
                print(f"  ✅ Short {short['day']+1} Scene {i}: {main_char}")
            except Exception as e:
                print(f"  ❌ Error: {e}")

    # Generate episode audio
    episode = data["episode"]
    for i, scene in enumerate(episode["scenes"]):
        chars = scene.get("chars", [])
        dialogues = scene.get("dialogue", [])

        for char, text in zip(chars, dialogues):
            voice = VOICES.get(char, VOICES["bip"])
            settings = VOICE_SETTINGS.get(char, VOICE_SETTINGS["bip"])
            out_file = audio_dir / f"episode_scene_{i}_{char}.mp3"

            if out_file.exists():
                print(f"  ⏭️  Exists: {out_file.name}")
                continue

            try:
                await generate_voice(text, voice, settings, str(out_file))
                print(f"  ✅ Episode Scene {i}: {char}")
            except Exception as e:
                print(f"  ❌ Error: {e}")

    print(f"\n✅ All audio generated for Week {week_num}")
    print(f"📁 Saved to: {audio_dir}")

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--week", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    config = load_config()

    if args.all:
        for week in range(1, 53):
            script_file = Path(config["paths"]["output"]) / f"week_{week}" / "scripts.json"
            if script_file.exists():
                asyncio.run(generate_all_audio(str(script_file), config))
            else:
                print(f"⚠️ Week {week} scripts not found, run generate_scripts.py first")
    else:
        script_file = Path(config["paths"]["output"]) / f"week_{args.week}" / "scripts.json"
        if not script_file.exists():
            print(f"❌ Scripts not found for week {args.week}")
            print("Run: python generate_scripts.py --week", args.week)
            sys.exit(1)
        asyncio.run(generate_all_audio(str(script_file), config))

if __name__ == "__main__":
    main()