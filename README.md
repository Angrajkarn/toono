# 🎬 Fully Automated Cartoon Channel - $0 Cost

**Zero manual work. Zero cost. Runs on any laptop OR free on GitHub Actions.**

## 🎯 What This Does

Every week, automatically:
1. **Writes** 5 Shorts + 1 Episode scripts (100+ story templates, no AI needed)
2. **Generates** voiceovers using FREE Microsoft Edge TTS (5 unique character voices)
3. **Renders** videos using MoviePy (pure Python, CPU only, no GPU)
4. **Uploads** to YouTube with proper tags, descriptions, COPPA compliance
5. **Schedules** next week automatically

**Characters:** Bip (Blue), Gloop (Green), Pip (Pink), Zap (Yellow), Snooze (Purple)

## 💰 Cost Breakdown

| Component | Cost | Tool |
|-----------|------|------|
| Animation | **$0** | MoviePy (Python) |
| Characters | **$0** | Code-generated SVG |
| Voiceovers | **$0** | Edge TTS (Microsoft) |
| Music/SFX | **$0** | YouTube Audio Library / Freesound |
| Hosting | **$0** | YouTube |
| Scheduling | **$0** | GitHub Actions / Windows Task Scheduler |
| **TOTAL** | **$0** | **Forever** |

## 🚀 Quick Start (5 Minutes)

### Option A: Run Locally (Windows/Mac/Linux)

```bash
# 1. Clone / Download this folder
cd cartoon_channel

# 2. Install Python packages
pip install -r requirements.txt

# 3. Install system dependencies
# Windows: choco install ffmpeg inkscape
# Mac: brew install ffmpeg inkscape
# Linux: sudo apt install ffmpeg inkscape

# 4. FIRST TIME SETUP (run once)
python run_pipeline.py --setup
# This generates assets, then opens browser for YouTube auth

# 5. TEST RUN (current week)
python run_pipeline.py
# Or specific week: python run_pipeline.py --week 1

# 6. AUTOMATE FOREVER
# Windows: Run setup_windows_scheduler.ps1 as Administrator
# Mac/Linux: Add to crontab: 0 10 * * 1 cd /path/to/cartoon_channel && python run_pipeline.py
```

### Option B: Run FREE on GitHub Actions (No Laptop Needed!)

1. **Push this folder to a GitHub repo**
2. **Add Secrets** in GitHub → Settings → Secrets → Actions:
   - `YOUTUBE_CLIENT_SECRET` = base64 encoded `client_secret.json`
   - `YOUTUBE_TOKEN` = base64 encoded `token.pkl` (after local auth once)
   - `CONFIG_YAML` = base64 encoded `config.yaml`
3. **Enable Actions** in repo Settings
4. **Done!** Runs every Monday automatically on GitHub's servers

**To encode secrets (run locally once):**
```bash
# Windows PowerShell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("client_secret.json")) | Set-Clipboard
[Convert]::ToBase64String([IO.File]::ReadAllBytes("token.pkl")) | Set-Clipboard
[Convert]::ToBase64String([IO.File]::ReadAllBytes("config.yaml")) | Set-Clipboard

# Mac/Linux
base64 -w 0 client_secret.json | pbcopy
base64 -w 0 token.pkl | pbcopy
base64 -w 0 config.yaml | pbcopy
```

## 📁 File Structure

```
cartoon_channel/
├── config.yaml              # 🔧 EDIT THIS - all settings
├── requirements.txt         # Python dependencies
├── run_pipeline.py          # 🎬 MASTER COMMAND - run this!
├── generate_assets.py       # Creates characters/backgrounds (run once)
├── generate_scripts.py      # Writes 5 shorts + 1 episode scripts
├── generate_audio.py        # FREE Edge TTS voiceovers
├── animate.py               # MoviePy video rendering (CPU only)
├── upload.py                # YouTube API upload
├── setup_windows_scheduler.ps1  # Windows auto-scheduler
├── .github/workflows/
│   └── cartoon-pipeline.yml # GitHub Actions (free cloud)
├── assets/
│   ├── characters/          # 5 SVG characters (auto-generated)
│   ├── backgrounds/         # 4 SVG backgrounds (auto-generated)
│   └── audio/               # Put free music/SFX here
├── output/
│   └── week_X/              # Generated each week
│       ├── scripts.json
│       ├── audio/
│       ├── short_1.mp4 ... short_5.mp4
│       └── episode.mp4
└── temp/                    # Temporary render files
```

## ⚙️ Configuration (Edit `config.yaml` Once)

```yaml
channel:
  name: "Your Channel Name"
  description: "Your description"
  made_for_kids: true  # REQUIRED for kids content

schedule:
  shorts_per_week: 5
  episode_per_week: 1
  upload_time: "10:00"
  timezone: "Asia/Kolkata"

characters:
  # 5 characters with colors & FREE Edge TTS voices
  bip:    {color: "#0099FF", voice: "en-US-GuyNeural"}
  gloop:  {color: "#00CC66", voice: "en-US-EricNeural"}
  pip:    {color: "#FF66CC", voice: "en-GB-SoniaNeural"}
  zap:    {color: "#FFCC00", voice: "en-US-JennyNeural"}
  snooze: {color: "#9966FF", voice: "en-US-RogerNeural"}
```

## 🎵 Free Audio Setup (One Time)

Download FREE music/SFX to `assets/audio/`:

| Source | What to Get | License |
|--------|-------------|---------|
| **YouTube Audio Library** | Happy/playful background loops | Free (in YT Studio) |
| **Incompetech** (Kevin MacLeod) | CC-BY music, credit in desc | Free with credit |
| **Pixabay Music** | Commercial-free tracks | Free |
| **Freesound.org** | Cartoon boing, pop, slide whistle | Free (account) |
| **ZapSplat** | Free tier sound effects | Free tier |

**Required files in `assets/audio/`:**
- `happy_loop.mp3` - Background music (~30s loop)
- `boing.mp3` - Jump/bounce
- `pop.mp3` - Appear/disappear
- `slide_whistle.mp3` - Fall/fail

## 🎬 Commands Reference

```bash
# MASTER - does everything for current week
python run_pipeline.py

# Specific week
python run_pipeline.py --week 5

# All 52 weeks (batch)
python run_pipeline.py --all

# First-time setup (assets + YouTube auth)
python run_pipeline.py --setup

# Run as daemon (checks daily)
python run_pipeline.py --schedule

# Individual steps (if needed)
python generate_scripts.py --week 1
python generate_audio.py --week 1
python animate.py --week 1
python upload.py --week 1

# YouTube auth only
python upload.py --auth
```

## 📅 Default Schedule

| Day | Content | Duration | Format |
|-----|---------|----------|--------|
| Mon | Short 1 | ~20 sec | Vertical (Shorts) |
| Tue | Short 2 | ~20 sec | Vertical (Shorts) |
| Wed | Short 3 | ~20 sec | Vertical (Shorts) |
| Thu | Short 4 | ~20 sec | Vertical (Shorts) |
| Fri | Short 5 | ~20 sec | Vertical (Shorts) |
| Sat | Episode | ~2 min | Horizontal |
| Sun | Rest / Compilation | - | - |

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError` | `pip install -r requirements.txt` |
| `cairosvg` / SVG errors | Install system deps: `ffmpeg`, `inkscape`, `libcairo2` |
| YouTube upload fails | Check `client_secret.json`, re-run `python upload.py --auth` |
| Render too slow | Reduce `threads` in config, use `quality: "fast"` |
| "Made for kids" error | Ensure `made_for_kids: true` in config |
| GitHub Actions timeout | Reduce video quality, or split into daily workflow |

## 🎨 Customizing Stories

Edit `generate_scripts.py` → `STORY_TEMPLATES` to add your own stories.
Each template has: `title`, `main_char` (or `chars` for episodes), `scenes[]` with `action`, `dialogue`, `duration`, `bg`.

No coding needed - just add more dictionaries to the list!

## 📊 Scaling Up

When you want higher quality:
1. **Characters**: Replace SVGs with rigged Spine/Creature animations
2. **Voices**: Upgrade to ElevenLabs (paid) for more expressive voices
3. **Animation**: Use Manim for math-based animations
4. **Backgrounds**: AI-generated (Stable Diffusion) or hand-drawn
5. **Music**: Custom composed

But the free version runs **forever at $0**!

## ⚖️ Legal / COPPA Compliance

- `selfDeclaredMadeForKids: true` set automatically
- No personalized ads on kids content
- No data collection from children
- All assets: MIT/CC0/Free licenses
- YouTube Audio Library music: Free for YouTube
- Edge TTS: Free for commercial use (Microsoft)

## 🤝 Contributing

Found a bug? Want more stories? Better animations?
This is 100% Python - modify any file!

## 📄 License

MIT License - Do whatever you want with this code.

---

**Built with ❤️ for creators who want to make kids happy without spending money.**

**Run once: `python run_pipeline.py --setup` → Then forget it exists.**