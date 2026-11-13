#!/usr/bin/env python3
"""
Generate ALL assets automatically - characters, backgrounds, audio placeholders
Run ONCE: python generate_assets.py
"""
import os
import svgwrite
import yaml
from pathlib import Path

def load_config():
    with open("config.yaml") as f:
        return yaml.safe_load(f)

def create_directories(config):
    for key, path in config["paths"].items():
        Path(path).mkdir(parents=True, exist_ok=True)

def generate_character_svg(name, color, config):
    """Generate a simple cutout-style character SVG programmatically"""
    dwg = svgwrite.Drawing(size=("300px", "450px"))

    # Body parts as separate groups for animation
    # Main body (torso)
    body = dwg.g(id=f"{name}_body")
    body.add(dwg.ellipse(center=(150, 280), r=(60, 80), fill=color, stroke='black', stroke_width=3))
    dwg.add(body)

    # Head
    head = dwg.g(id=f"{name}_head")
    head.add(dwg.circle(center=(150, 130), r=55, fill=color, stroke='black', stroke_width=3))
    # Eyes
    head.add(dwg.circle(center=(125, 115), r=12, fill='white', stroke='black', stroke_width=2))
    head.add(dwg.circle(center=(125, 115), r=6, fill='black'))
    head.add(dwg.circle(center=(175, 115), r=12, fill='white', stroke='black', stroke_width=2))
    head.add(dwg.circle(center=(175, 115), r=6, fill='black'))
    # Mouth (simple smile)
    head.add(dwg.path(d="M 120 155 Q 150 175 180 155", fill='none', stroke='black', stroke_width=3))
    dwg.add(head)

    # Arms
    arm_l = dwg.g(id=f"{name}_arm_l")
    arm_l.add(dwg.path(d="M 90 250 Q 50 300 40 350", stroke=color, stroke_width=15, fill='none', stroke_linecap='round'))
    dwg.add(arm_l)

    arm_r = dwg.g(id=f"{name}_arm_r")
    arm_r.add(dwg.path(d="M 210 250 Q 250 300 260 350", stroke=color, stroke_width=15, fill='none', stroke_linecap='round'))
    dwg.add(arm_r)

    # Legs
    leg_l = dwg.g(id=f"{name}_leg_l")
    leg_l.add(dwg.path(d="M 120 360 L 110 430", stroke=color, stroke_width=15, fill='none', stroke_linecap='round'))
    dwg.add(leg_l)

    leg_r = dwg.g(id=f"{name}_leg_r")
    leg_r.add(dwg.path(d="M 180 360 L 190 430", stroke=color, stroke_width=15, fill='none', stroke_linecap='round'))
    dwg.add(leg_r)

    # Character-specific details
    if name == "pip":
        # Glasses
        glasses = dwg.g(id=f"{name}_glasses")
        glasses.add(dwg.circle(center=(125, 115), r=18, fill='none', stroke='black', stroke_width=2))
        glasses.add(dwg.circle(center=(175, 115), r=18, fill='none', stroke='black', stroke_width=2))
        glasses.add(dwg.line(start=(143, 115), end=(157, 115), stroke='black', stroke_width=2))
        dwg.add(glasses)
    elif name == "zap":
        # Lightning bolt on chest
        bolt = dwg.g(id=f"{name}_bolt")
        bolt.add(dwg.polyline(points=[(150, 200), (140, 240), (145, 240), (135, 280), (155, 230), (145, 230), (150, 200)],
                                fill='#FFCC00', stroke='black', stroke_width=2))
        dwg.add(bolt)
    elif name == "snooze":
        # Sleep bubble
        bubble = dwg.g(id=f"{name}_bubble")
        bubble.add(dwg.text("Zzz", insert=(210, 80), font_size=24, fill='#9966FF', font_family='Arial', font_weight='bold'))
        dwg.add(bubble)
    elif name == "gloop":
        # Wobble lines
        wobble = dwg.g(id=f"{name}_wobble")
        wobble.add(dwg.path(d="M 80 280 Q 60 300 70 330", stroke=color, stroke_width=2, fill='none', opacity=0.5))
        wobble.add(dwg.path(d="M 220 280 Q 240 300 230 330", stroke=color, stroke_width=2, fill='none', opacity=0.5))
        dwg.add(wobble)

    return dwg

def generate_background_svg(name, color, config):
    """Generate simple background SVGs"""
    dwg = svgwrite.Drawing(size=("1920px", "1080px"))
    dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), fill=color))

    # Add simple decorative elements
    if name == "room":
        # Simple furniture silhouettes
        dwg.add(dwg.rect(insert=(100, 700), size=(300, 300), fill='#D4A574', stroke='black', stroke_width=2))  # couch
        dwg.add(dwg.rect(insert=(1500, 750), size=(200, 200), fill='#8B7355', stroke='black', stroke_width=2))  # table
    elif name == "park":
        # Trees
        for x in [200, 600, 1200, 1600]:
            dwg.add(dwg.rect(insert=(x, 600), size=(40, 300), fill='#8B7355'))  # trunk
            dwg.add(dwg.circle(center=(x+20, 550), r=80, fill='#2E7D32', stroke='black', stroke_width=2))  # leaves
    elif name == "kitchen":
        dwg.add(dwg.rect(insert=(100, 600), size=(500, 400), fill='#E0E0E0', stroke='black', stroke_width=2))  # counter
        dwg.add(dwg.rect(insert=(1300, 650), size=(150, 150), fill='#FFD54F', stroke='black', stroke_width=2))  # fridge
    elif name == "bedroom":
        dwg.add(dwg.rect(insert=(300, 650), size=(400, 300), fill='#FFF9C4', stroke='black', stroke_width=2))  # bed
        dwg.add(dwg.rect(insert=(300, 650), size=(400, 50), fill='#FFCCBC', stroke='black', stroke_width=2))  # pillow

    return dwg

def generate_all_assets():
    config = load_config()
    create_directories(config)

    print("🎨 Generating character assets...")
    for name, char_config in config["characters"].items():
        svg_path = Path(config["paths"]["assets"]) / "characters" / f"{name}.svg"
        dwg = generate_character_svg(name, char_config["color"], config)
        dwg.saveas(str(svg_path))
        print(f"  ✅ {name}.svg")

    print("\n🏞️ Generating background assets...")
    bg_colors = {
        "room": "#FFF8E7",
        "park": "#E8F5E9",
        "kitchen": "#FFF3E0",
        "bedroom": "#F3E5F5"
    }
    for name, color in bg_colors.items():
        svg_path = Path(config["paths"]["assets"]) / "backgrounds" / f"{name}.svg"
        dwg = generate_background_svg(name, color, config)
        dwg.saveas(str(svg_path))
        print(f"  ✅ {name}.svg")

    print("\n🎵 Creating audio placeholder info...")
    audio_dir = Path(config["paths"]["assets"]) / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    # Create a simple silence MP3 for background music placeholder
    # (Real music downloaded separately from YouTube Audio Library)
    readme = audio_dir / "README.txt"
    readme.write_text("""FREE AUDIO SOURCES (Download manually once):

BACKGROUND MUSIC:
- YouTube Audio Library (FREE in YouTube Studio) → Search "happy", "playful", "kids"
- Incompetech.com (Kevin MacLeod) → CC-BY, credit in description
- Pixabay Music → Free for commercial use
- StreamBeats (Harris Heller) → Free for creators

SOUND EFFECTS:
- Freesound.org (free account) → Search "cartoon boing", "pop", "slide whistle"
- ZapSplat.com (free tier) → Cartoon sounds
- BBC Sound Effects → Free for personal/educational

PLACE FILES HERE:
- happy_loop.mp3 (background music, ~30s loop)
- boing.mp3 (jump/bounce)
- pop.mp3 (appear/disappear)
- slide_whistle.mp3 (fall/fail)
- laugh.mp3 (kids laughing)
""")
    print(f"  ✅ Audio README created at {readme}")

    print("\n✅ ALL ASSETS GENERATED!")
    print("📁 Check assets/ folder")
    print("📥 Download free music/SFX to assets/audio/ (see README.txt)")

if __name__ == "__main__":
    generate_all_assets()