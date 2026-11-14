#!/usr/bin/env python3
"""
Render ALL videos automatically using MoviePy (Pure Python, CPU only)
Run: python animate.py --week 1
"""
import os
import json
import math
import yaml
import subprocess
from pathlib import Path
from moviepy.editor import *
from moviepy.video.tools.drawing import color_gradient

def create_text_clip(text, video_type="short", duration=4):
    """Create text clip using PIL (no ImageMagick needed)"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        import numpy as np

        # Settings based on video type
        if video_type == "short":
            width, height = 700, 200
            fontsize = 36
        else:
            width, height = 1000, 250
            fontsize = 42

        # Create transparent image
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Load font
        font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
        try:
            font = ImageFont.truetype(font_path, fontsize)
        except Exception:
            font = ImageFont.load_default()

        # Calculate text position (centered)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (width - text_width) // 2
        y = (height - text_height) // 2

        # Draw stroke (white outline)
        stroke_width = 3
        for dx in range(-stroke_width, stroke_width + 1):
            for dy in range(-stroke_width, stroke_width + 1):
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), text, font=font, fill='white')

        # Draw main text (black)
        draw.text((x, y), text, font=font, fill='black')

        # Convert to numpy array for MoviePy
        img_array = np.array(img)

        # Create ImageClip
        txt_clip = ImageClip(img_array, transparent=True).set_duration(duration)
        return txt_clip
    except Exception as e:
        print(f"  ⚠️ Failed to create text clip: {e}")
        return None


def load_config():
    with open("config.yaml") as f:
        return yaml.safe_load(f)

def svg_to_png(svg_path, png_path, size):
    """Convert SVG to PNG using cairosvg"""
    try:
        import cairosvg
        cairosvg.svg2png(url=str(svg_path), write_to=str(png_path),
                         output_width=size[0], output_height=size[1])
        return True
    except Exception as e:
        print(f"  ⚠️ cairosvg failed: {e}, trying Inkscape...")
        # Fallback to Inkscape if available
        try:
            subprocess.run(["inkscape", str(svg_path), "--export-filename=" + str(png_path),
                          f"--export-width={size[0]}", f"--export-height={size[1]}"],
                         check=True, capture_output=True)
            return True
        except:
            print(f"  ❌ Could not convert {svg_path}")
            return False

def get_character_size(char_name, config, video_type):
    """Get character size based on video type"""
    if video_type == "short":
        return (300, 450)  # Larger for vertical
    else:
        return (250, 380)  # Smaller for horizontal

def create_character_clips(config, video_type):
    """Pre-render all character SVGs to PNG clips"""
    assets_dir = Path(config["paths"]["assets"])
    temp_dir = Path(config["paths"]["temp"])
    temp_dir.mkdir(parents=True, exist_ok=True)

    char_clips = {}
    char_size = None

    for name, char_config in config["characters"].items():
        svg_path = assets_dir / "characters" / f"{name}.svg"
        if not svg_path.exists():
            continue

        size = get_character_size(name, config, video_type)
        if char_size is None:
            char_size = size

        png_path = temp_dir / f"{name}_{video_type}.png"
        if svg_to_png(svg_path, png_path, size):
            # Create base clip (will be duplicated and animated per scene)
            clip = ImageClip(str(png_path)).set_duration(1)
            char_clips[name] = clip

    return char_clips, char_size

def create_background_clip(bg_name, config, video_type):
    """Create background clip for video type"""
    assets_dir = Path(config["paths"]["assets"])
    temp_dir = Path(config["paths"]["temp"])

    if video_type == "short":
        # For shorts, use vertical crop of horizontal background
        svg_path = assets_dir / "backgrounds" / f"{bg_name}.svg"
        png_path = temp_dir / f"{bg_name}_short.png"
        if svg_to_png(svg_path, png_path, (1080, 1920)):
            return ImageClip(str(png_path))
    else:
        svg_path = assets_dir / "backgrounds" / f"{bg_name}.svg"
        png_path = temp_dir / f"{bg_name}_episode.png"
        if svg_to_png(svg_path, png_path, (1920, 1080)):
            return ImageClip(str(png_path))

    # Fallback solid color
    if video_type == "short":
        return ColorClip((1080, 1920), color=(255, 248, 231))
    else:
        return ColorClip((1920, 1080), color=(255, 248, 231))

def animate_character(char_clip, scene, char_name, duration, video_type, char_size):
    """Apply animation to character based on action keywords"""
    action = scene.get("action", "").lower()
    dialogue = scene.get("dialogue", "")

    # Position defaults
    if video_type == "short":
        center_x, center_y = 540, 1200  # Vertical center
    else:
        center_x, center_y = 960, 600   # Horizontal center

    # Animation functions based on action keywords
    def pos_func(t):
        x, y = center_x, center_y

        if "run" in action or "zoom" in action or "race" in action or "chase" in action:
            # Horizontal movement
            x = center_x + math.sin(t * 2) * 200
        elif "jump" in action or "bounce" in action or "hop" in action:
            # Vertical bounce
            y = center_y - abs(math.sin(t * 3)) * 100
        elif "shake" in action or "tremble" in action or "explode" in action:
            # Shake
            x = center_x + math.sin(t * 20) * 15
            y = center_y + math.cos(t * 17) * 10
        elif "float" in action or "fly" in action or "lift" in action:
            # Gentle float
            y = center_y - 50 + math.sin(t) * 20
            x = center_x + math.cos(t * 0.7) * 30
        elif "sleep" in action or "nap" in action or "dream" in action:
            # Gentle sway
            x = center_x + math.sin(t * 0.5) * 10
            y = center_y + math.cos(t * 0.3) * 5
        elif "spin" in action or "twirl" in action:
            # Rotation handled separately
            pass
        else:
            # Default subtle breathing
            scale = 1 + 0.02 * math.sin(t * 2)
            return (x, y), scale

        return (x, y), 1.0

    # Apply position animation
    animated = char_clip.set_position(lambda t: pos_func(t)[0])

    # Apply scale animation (breathing)
    def scale_func(t):
        _, scale = pos_func(t)
        return scale

    animated = animated.resize(scale_func)

    # Add dialogue bubble if there's dialogue - use PIL instead of TextClip (no ImageMagick needed)
    if dialogue:
        txt_clip = create_text_clip(
            dialogue,
            video_type=video_type,
            duration=duration
        )
        if txt_clip:
            # Position above character
            if video_type == "short":
                txt_clip = txt_clip.set_position(("center", 200))
            else:
                txt_clip = txt_clip.set_position(("center", 150))
            # Combine character + text
            animated = CompositeVideoClip([animated, txt_clip])

    return animated.set_duration(duration)

def create_silent_audio(duration, output_path):
    """Create a silent audio file as fallback"""
    import subprocess
    try:
        subprocess.run([
            "ffmpeg", "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo",
            "-t", str(duration), "-c:a", "libmp3lame", "-b:a", "128k",
            "-y", str(output_path)
        ], check=True, capture_output=True)
        return True
    except Exception:
        return False


def get_valid_audio_file(audio_file, expected_duration):
    """Get a valid audio file, create silent fallback if needed"""
    if audio_file.exists() and audio_file.stat().st_size > 1000:
        # Validate with ffprobe
        import subprocess
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", str(audio_file)],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                dur = float(result.stdout.strip())
                if dur > 0:
                    return str(audio_file)
        except Exception:
            pass

    # Create silent fallback
    fallback = audio_file.with_suffix('.silent.mp3')
    if create_silent_audio(expected_duration + 0.5, fallback):
        return str(fallback)
    return None


def render_short(short_data, config, char_clips, bg_clips):
    """Render a single short video"""
    scenes = short_data["scenes"]
    main_char = short_data["main_char"]
    week_num = short_data.get("week", 1)
    day = short_data["day"]

    clips = []
    audio_dir = Path(config["paths"]["output"]) / f"week_{week_num}" / "audio"

    for i, scene in enumerate(scenes):
        duration = scene.get("duration", 4)
        bg_name = scene.get("bg", "room")

        # Load audio to get exact duration
        audio_file = audio_dir / f"short_{day+1}_scene_{i}.mp3"
        valid_audio = get_valid_audio_file(audio_file, duration)

        if valid_audio:
            audio_clip = AudioFileClip(valid_audio)
            duration = max(duration, audio_clip.duration + 0.5)  # Small padding
        else:
            print(f"  ⚠️ No valid audio for scene {i}, using silent fallback")

        # Get background
        bg = bg_clips.get(bg_name)
        if bg is None:
            bg = create_background_clip(bg_name, config, "short")

        bg = bg.set_duration(duration)

        # Get character
        char_base = char_clips.get(main_char)
        if char_base is None:
            print(f"  ❌ Character {main_char} not found")
            continue

        # Animate character
        char_animated = animate_character(char_base, scene, main_char, duration, "short", None)

        # Combine
        scene_clip = CompositeVideoClip([bg, char_animated])

        # Add audio if available
        if valid_audio:
            audio_clip = AudioFileClip(valid_audio)
            scene_clip = scene_clip.set_audio(audio_clip)

        clips.append(scene_clip)

    if not clips:
        return None

    # Concatenate all scenes
    final = concatenate_videoclips(clips, method="compose")

    # Add background music
    music_file = Path(config["paths"]["assets"]) / "audio" / "happy_loop.mp3"
    if music_file.exists():
        music = AudioFileClip(str(music_file)).volumex(0.08)
        music = music.audio_loop(duration=final.duration)
        final = final.set_audio(CompositeAudioClip([final.audio, music]))

    return final

def render_episode(ep_data, config, char_clips, bg_clips):
    """Render a weekly episode"""
    scenes = ep_data["scenes"]
    week_num = ep_data.get("week", 1)

    clips = []
    audio_dir = Path(config["paths"]["output"]) / f"week_{week_num}" / "audio"

    for i, scene in enumerate(scenes):
        duration = scene.get("duration", 6)
        bg_name = scene.get("bg", "room")
        chars = scene.get("chars", [])
        dialogues = scene.get("dialogue", [])

        # Load longest audio for timing
        max_duration = duration
        audio_clips = []
        for char, dialogue in zip(chars, dialogues):
            audio_file = audio_dir / f"episode_scene_{i}_{char}.mp3"
            valid_audio = get_valid_audio_file(audio_file, duration)
            if valid_audio:
                audio = AudioFileClip(valid_audio)
                audio_clips.append((char, audio))
                max_duration = max(max_duration, audio.duration + 0.5)
            else:
                print(f"  ⚠️ No valid audio for episode scene {i} char {char}")

        duration = max_duration

        # Get background
        bg = bg_clips.get(bg_name)
        if bg is None:
            bg = create_background_clip(bg_name, config, "episode")
        bg = bg.set_duration(duration)

        # Animate all characters in scene
        char_layers = []
        for char, dialogue in zip(chars, dialogues):
            char_base = char_clips.get(char)
            if char_base is None:
                continue

            # Create scene copy for this character
            char_scene = scene.copy()
            char_scene["dialogue"] = dialogue

            char_animated = animate_character(char_base, char_scene, char, duration, "episode", None)

            # Add character-specific audio
            for c, audio in audio_clips:
                if c == char:
                    char_animated = char_animated.set_audio(audio)
                    break

            char_layers.append(char_animated)

        # Composite all characters on background
        if char_layers:
            scene_composite = CompositeVideoClip([bg] + char_layers)
        else:
            scene_composite = bg

        clips.append(scene_composite)

    if not clips:
        return None

    # Concatenate
    final = concatenate_videoclips(clips, method="compose")

    # Add background music
    music_file = Path(config["paths"]["assets"]) / "audio" / "happy_loop.mp3"
    if music_file.exists():
        music = AudioFileClip(str(music_file)).volumex(0.08)
        music = music.audio_loop(duration=final.duration)
        final = final.set_audio(CompositeAudioClip([final.audio, music]))

    return final

def render_week(week_num, config):
    """Render all videos for a week"""
    script_file = Path(config["paths"]["output"]) / f"week_{week_num}" / "scripts.json"
    if not script_file.exists():
        print(f"❌ Scripts not found for week {week_num}")
        return

    with open(script_file) as f:
        data = json.load(f)

    output_dir = Path(config["paths"]["output"]) / f"week_{week_num}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Pre-render character and background clips
    print(f"🎬 Preparing assets for Week {week_num}...")
    short_chars, _ = create_character_clips(config, "short")
    episode_chars, _ = create_character_clips(config, "episode")

    # Backgrounds
    bg_names = ["room", "park", "kitchen", "bedroom"]
    short_bgs = {name: create_background_clip(name, config, "short") for name in bg_names}
    episode_bgs = {name: create_background_clip(name, config, "episode") for name in bg_names}

    # Render shorts
    print(f"📱 Rendering {len(data['shorts'])} Shorts...")
    for short in data["shorts"]:
        day = short["day"]
        out_file = output_dir / f"short_{day+1}.mp4"

        if out_file.exists():
            print(f"  ⏭️  Exists: short_{day+1}.mp4")
            continue

        print(f"  🎥 Rendering Short {day+1}: {short['title']}...")
        final = render_short(short, config, short_chars, short_bgs)

        if final:
            final.write_videofile(
                str(out_file),
                fps=config["video"]["shorts"]["fps"],
                codec=config["render"]["codec"],
                audio_codec=config["render"]["audio_codec"],
                preset=config["render"]["quality"],
                threads=config["render"]["threads"],
                logger=None
            )
            print(f"  ✅ Saved: {out_file}")

    # Render episode
    ep = data["episode"]
    out_file = output_dir / "episode.mp4"

    if not out_file.exists():
        print(f"🎞️ Rendering Episode: {ep['title']}...")
        final = render_episode(ep, config, episode_chars, episode_bgs)

        if final:
            final.write_videofile(
                str(out_file),
                fps=config["video"]["episode"]["fps"],
                codec=config["render"]["codec"],
                audio_codec=config["render"]["audio_codec"],
                preset=config["render"]["quality"],
                threads=config["render"]["threads"],
                logger=None
            )
            print(f"  ✅ Saved: {out_file}")
    else:
        print(f"  ⏭️  Exists: episode.mp4")

    print(f"\n✅ Week {week_num} rendering complete!")
    print(f"📁 Output: {output_dir}")

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
                render_week(week, config)
            else:
                print(f"⚠️ Week {week} scripts not found")
    else:
        render_week(args.week, config)

if __name__ == "__main__":
    main()