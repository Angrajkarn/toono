#!/usr/bin/env python3
"""
Upload ALL videos to YouTube automatically using YouTube Data API v3 (FREE)
Run: python upload.py --week 1

SETUP (one-time):
1. Go to https://console.cloud.google.com/
2. Create project → Enable "YouTube Data API v3"
3. Create OAuth 2.0 credentials → Download as client_secret.json
4. Place client_secret.json in this folder
5. Run once: python upload.py --auth (to authorize)
"""
import os
import json
import pickle
import yaml
import sys
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def load_config():
    with open("config.yaml") as f:
        return yaml.safe_load(f)

def get_authenticated_service(config):
    """Get authenticated YouTube service"""
    creds = None
    token_file = "token.pkl"

    # Load existing token
    if os.path.exists(token_file):
        with open(token_file, "rb") as f:
            creds = pickle.load(f)

    # Refresh or get new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            client_secret = "client_secret.json"
            if not os.path.exists(client_secret):
                print(f"❌ {client_secret} not found!")
                print("1. Go to https://console.cloud.google.com/")
                print("2. Create project → Enable YouTube Data API v3")
                print("3. Create OAuth 2.0 credentials (Desktop app)")
                print("4. Download as client_secret.json")
                print("5. Place in this folder")
                sys.exit(1)

            flow = InstalledAppFlow.from_client_secrets_file(client_secret, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save token for next run
        with open(token_file, "wb") as f:
            pickle.dump(creds, f)

    return build("youtube", "v3", credentials=creds)

def upload_video(youtube, file_path, title, description, tags, is_short, config):
    """Upload single video to YouTube"""
    body = {
        "snippet": {
            "title": title[:100],  # YouTube limit
            "description": description,
            "tags": tags,
            "categoryId": config["youtube"]["category_id"],
            "defaultLanguage": config["channel"]["language"]
        },
        "status": {
            "privacyStatus": config["youtube"]["privacy"],
            "selfDeclaredMadeForKids": config["channel"]["made_for_kids"],
            "notifySubscribers": True
        }
    }

    # Shorts need #shorts in title or description
    if is_short and config["youtube"]["shorts_hashtag"]:
        if "#shorts" not in description.lower():
            body["snippet"]["description"] = "#shorts\n" + description

    media = MediaFileUpload(
        file_path,
        chunksize=-1,
        resumable=True,
        mimetype="video/mp4"
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  📤 Upload progress: {int(status.progress() * 100)}%")

    video_id = response["id"]
    url = f"https://youtube.com/shorts/{video_id}" if is_short else f"https://youtube.com/watch?v={video_id}"

    # Add to playlist if configured (optional)
    return {"id": video_id, "url": url, "title": title}

def upload_week(week_num, config, youtube=None):
    """Upload all videos for a week"""
    output_dir = Path(config["paths"]["output"]) / f"week_{week_num}"
    if not output_dir.exists():
        print(f"❌ No output directory for week {week_num}")
        return

    if youtube is None:
        youtube = get_authenticated_service(config)

    print(f"📤 Uploading Week {week_num} videos...")

    # Load scripts for metadata
    script_file = output_dir / "scripts.json"
    with open(script_file) as f:
        data = json.load(f)

    base_tags = config["youtube"]["tags_base"]
    channel_name = config["channel"]["name"]

    # Upload shorts (Mon-Fri)
    for short in data["shorts"]:
        day = short["day"]
        video_file = output_dir / f"short_{day+1}.mp4"

        if not video_file.exists():
            print(f"  ⚠️  Missing: short_{day+1}.mp4")
            continue

        title = f"{short['title']} 😂 | {channel_name}"
        description = f"""{short['title']}

Daily funny cartoon for kids! 🎬
Join Bip, Gloop, Pip, Zap & Snooze for new adventures every day!

Subscribe for more: [Your Channel URL]

#cartoons #kids #funny #animation #shorts"""

        tags = base_tags + [short["main_char"], f"day{day+1}"]

        try:
            result = upload_video(youtube, str(video_file), title, description, tags, True, config)
            print(f"  ✅ Short {day+1}: {result['url']}")
        except Exception as e:
            print(f"  ❌ Short {day+1} failed: {e}")

    # Upload episode (Saturday)
    ep = data["episode"]
    video_file = output_dir / "episode.mp4"

    if video_file.exists():
        title = f"{ep['title']} 🎬 | {channel_name}"
        description = f"""{ep['title']}

Weekly cartoon adventure with all 5 friends! 🌟
Bip, Gloop, Pip, Zap & Snooze together in one big story!

New shorts every Mon-Fri, new episode every Saturday!
Subscribe so you don't miss any: [Your Channel URL]

#cartoons #kids #funny #animation #episode #weekly"""

        tags = base_tags + ["episode", "weekly", "allcharacters"]

        try:
            result = upload_video(youtube, str(video_file), title, description, tags, False, config)
            print(f"  ✅ Episode: {result['url']}")
        except Exception as e:
            print(f"  ❌ Episode failed: {e}")
    else:
        print(f"  ⚠️  Missing: episode.mp4")

    print(f"\n✅ Week {week_num} upload complete!")

def authorize_only():
    """Just run authorization flow"""
    config = load_config()
    youtube = get_authenticated_service(config)
    print("✅ Authorization successful! Token saved.")
    return youtube

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--week", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--auth", action="store_true", help="Just authorize (run once)")
    args = parser.parse_args()

    config = load_config()

    if args.auth:
        authorize_only()
        return

    youtube = get_authenticated_service(config)

    if args.all:
        for week in range(1, 53):
            output_dir = Path(config["paths"]["output"]) / f"week_{week}"
            if output_dir.exists():
                upload_week(week, config, youtube)
            else:
                print(f"⚠️ Week {week} not rendered yet")
    else:
        upload_week(args.week, config, youtube)

if __name__ == "__main__":
    main()