#!/usr/bin/env python3
"""
🧪 QUICK TEST - Verifies entire pipeline works in ~2 minutes
Run: python test_pipeline.py
"""
import sys
import subprocess
import yaml
from pathlib import Path

def run(cmd, desc):
    print(f"\n🔄 {desc}...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        print(f"❌ FAILED: {result.stderr[:500]}")
        return False
    print(f"✅ {desc}")
    return True

def main():
    print("🧪 TESTING FULL PIPELINE (Week 1)...")
    print("="*50)

    # Load config
    with open("config.yaml") as f:
        config = yaml.safe_load(f)

    # Create dirs
    for p in config["paths"].values():
        Path(p).mkdir(parents=True, exist_ok=True)

    tests = [
        ([sys.executable, "generate_assets.py"], "Generate assets"),
        ([sys.executable, "generate_scripts.py", "--week=1"], "Generate scripts"),
        ([sys.executable, "generate_audio.py", "--week=1"], "Generate audio"),
        ([sys.executable, "animate.py", "--week=1"], "Render videos"),
    ]

    for cmd, desc in tests:
        if not run(cmd, desc):
            print(f"\n❌ TEST FAILED at: {desc}")
            sys.exit(1)

    # Verify outputs
    out_dir = Path(config["paths"]["output"]) / "week_1"
    expected = [
        "scripts.json",
        "short_1.mp4", "short_2.mp4", "short_3.mp4", "short_4.mp4", "short_5.mp4",
        "episode.mp4",
    ]

    print(f"\n📁 Verifying outputs in {out_dir}...")
    all_ok = True
    for f in expected:
        path = out_dir / f
        if path.exists():
            size_mb = path.stat().st_size / (1024*1024)
            print(f"  ✅ {f} ({size_mb:.1f} MB)")
        else:
            print(f"  ❌ MISSING: {f}")
            all_ok = False

    if all_ok:
        print("\n" + "="*50)
        print("🎉 ALL TESTS PASSED!")
        print("✅ Pipeline is working perfectly")
        print(f"📹 Videos ready in: {out_dir}")
        print("\nNext steps:")
        print("  1. Add client_secret.json for YouTube")
        print("  2. Run: python upload.py --auth")
        print("  3. Run: python run_pipeline.py")
        print("  4. Automate: python run_pipeline.py --schedule")
    else:
        print("\n⚠️ Some files missing - check errors above")
        sys.exit(1)

if __name__ == "__main__":
    main()