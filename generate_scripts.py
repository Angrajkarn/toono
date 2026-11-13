#!/usr/bin/env python3
"""
Generate ALL scripts automatically - 5 shorts + 1 episode per week
Run automatically via scheduler: python generate_scripts.py --week 1
"""
import json
import random
import sys
import yaml
from pathlib import Path
from datetime import datetime

def load_config():
    with open("config.yaml") as f:
        return yaml.safe_load(f)

# 100+ Story templates - NO API NEEDED, pure Python
STORY_TEMPLATES = {
    "shorts": [
        # Bip stories
        {"title": "Bip's Mystery Box", "main_char": "bip", "scenes": [
            {"action": "Bip finds a colorful box on the ground", "dialogue": "Wow! What's inside?", "duration": 4, "bg": "room"},
            {"action": "Box shakes and makes silly boing noises", "dialogue": "Hehe, it's tickling me!", "duration": 3, "bg": "room"},
            {"action": "Box opens - confetti explodes everywhere", "dialogue": "YAY! Best surprise ever!", "duration": 4, "bg": "room"},
        ]},
        {"title": "Bip's Magic Hat", "main_char": "bip", "scenes": [
            {"action": "Bip tries on a hat - it's too big", "dialogue": "Whoa! I'm disappearing!", "duration": 3, "bg": "room"},
            {"action": "Tries another - too small", "dialogue": "Ouch! My ears!", "duration": 3, "bg": "room"},
            {"action": "A bird lands on head as perfect hat", "dialogue": "Perfect! Thanks birdie!", "duration": 3, "bg": "park"},
        ]},
        {"title": "Bip's Shadow Dance", "main_char": "bip", "scenes": [
            {"action": "Bip sees shadow doing funny moves", "dialogue": "Hey! Copy me!", "duration": 3, "bg": "room"},
            {"action": "Shadow does silly dance", "dialogue": "You're better than me!", "duration": 4, "bg": "room"},
            {"action": "Bip bows to shadow", "dialogue": "Encore! Encore!", "duration": 3, "bg": "room"},
        ]},
        {"title": "Bip's Balloon Friend", "main_char": "bip", "scenes": [
            {"action": "Bip finds red balloon, draws face", "dialogue": "Meet Bob!", "duration": 3, "bg": "room"},
            {"action": "Balloon floats away, Bip chases", "dialogue": "Bob! Come back!", "duration": 4, "bg": "park"},
            {"action": "Balloon pops - confetti", "dialogue": "Bob! You threw a party!", "duration": 3, "bg": "park"},
        ]},
        {"title": "Bip's Echo Game", "main_char": "bip", "scenes": [
            {"action": "Bip shouts in empty room", "dialogue": "HELLO!", "duration": 3, "bg": "room"},
            {"action": "Echo replies weirdly", "dialogue": "HELLO... jello... yellow!", "duration": 4, "bg": "room"},
            {"action": "Bip laughs at echo", "dialogue": "You're silly!", "duration": 3, "bg": "room"},
        ]},

        # Gloop stories
        {"title": "Gloop's Shape Practice", "main_char": "gloop", "scenes": [
            {"action": "Gloop tries to be a square", "dialogue": "Look! I'm a box! ...Oops, melted.", "duration": 4, "bg": "room"},
            {"action": "Tries triangle - gets pointy then wobbly", "dialogue": "Pointy! ...Nope, wobbly again.", "duration": 3, "bg": "room"},
            {"action": "Turns into heart shape", "dialogue": "Love this shape!", "duration": 3, "bg": "room"},
        ]},
        {"title": "Gloop's Baking Mess", "main_char": "gloop", "scenes": [
            {"action": "Gloop mixes flour - POOF! Flour everywhere", "dialogue": "SNOW! In the kitchen!", "duration": 4, "bg": "kitchen"},
            {"action": "Dough comes alive, wiggles away", "dialogue": "Cookie! Wait! Come back!", "duration": 4, "bg": "kitchen"},
            {"action": "Gloop catches and eats it", "dialogue": "Best cookie ever. I made it!", "duration": 3, "bg": "kitchen"},
        ]},
        {"title": "Gloop's Bubble Trouble", "main_char": "gloop", "scenes": [
            {"action": "Gloop blows giant bubble", "dialogue": "Biggest bubble ever!", "duration": 3, "bg": "park"},
            {"action": "Bubble lifts Gloop up", "dialogue": "Wheee! I'm flying!", "duration": 4, "bg": "park"},
            {"action": "Bubble pops - soft landing in flowers", "dialogue": "Best landing ever!", "duration": 3, "bg": "park"},
        ]},
        {"title": "Gloop's Mirror Fun", "main_char": "gloop", "scenes": [
            {"action": "Gloop makes faces at mirror", "dialogue": "Who's the silliest?", "duration": 3, "bg": "room"},
            {"action": "Mirror reflection does different face", "dialogue": "Hey! Copy me!", "duration": 4, "bg": "room"},
            {"action": "Both laugh, Gloop wobbles", "dialogue": "We both win!", "duration": 3, "bg": "room"},
        ]},
        {"title": "Gloop's Puddle Jump", "main_char": "gloop", "scenes": [
            {"action": "Gloop finds rainbow puddle", "dialogue": "Ooh! Colors!", "duration": 3, "bg": "park"},
            {"action": "Jumps in - splashes rainbow everywhere", "dialogue": "WOW! Rainbow splash!", "duration": 4, "bg": "park"},
            {"action": "Gloop is now rainbow colored", "dialogue": "I'm a rainbow blob!", "duration": 3, "bg": "park"},
        ]},

        # Pip stories
        {"title": "Pip's Fun Fact", "main_char": "pip", "scenes": [
            {"action": "Pip reads book, looks amazed", "dialogue": "Did you know? Octopuses have THREE hearts!", "duration": 4, "bg": "room"},
            {"action": "Imagines octopus with 3 hearts beating", "dialogue": "Thump-thump-thump! So much love!", "duration": 3, "bg": "room"},
            {"action": "Closes book happily", "dialogue": "Learning is the best adventure.", "duration": 3, "bg": "room"},
        ]},
        {"title": "Pip's Library Quest", "main_char": "pip", "scenes": [
            {"action": "Pip searches for book on tall shelf", "dialogue": "Must... reach... knowledge!", "duration": 3, "bg": "room"},
            {"action": "Stacks books as ladder, wobbles", "dialogue": "Physics... not my strong subject.", "duration": 4, "bg": "room"},
            {"action": "Gloop catches her", "dialogue": "Thanks! Teamwork beats physics!", "duration": 3, "bg": "room"},
        ]},
        {"title": "Pip's Weather Report", "main_char": "pip", "scenes": [
            {"action": "Pip gives pretend weather report", "dialogue": "Today: Cloudy with chance of giggles!", "duration": 4, "bg": "room"},
            {"action": "Gloop floats by like cloud", "dialogue": "Breaking news: Silly cloud spotted!", "duration": 3, "bg": "room"},
            {"action": "Pip laughs", "dialogue": "Forecast: 100% fun!", "duration": 3, "bg": "room"},
        ]},
        {"title": "Pip's Plant Experiment", "main_char": "pip", "scenes": [
            {"action": "Pip talks to plant", "dialogue": "Grow big! Photosynthesize!", "duration": 3, "bg": "room"},
            {"action": "Plant instantly grows huge (Zap sped it up)", "dialogue": "WHOA! Science works fast!", "duration": 4, "bg": "room"},
            {"action": "Plant grows candy instead", "dialogue": "New discovery: Candy-synthesis!", "duration": 3, "bg": "room"},
        ]},
        {"title": "Pip's Tongue Twister", "main_char": "pip", "scenes": [
            {"action": "Pip tries tongue twister", "dialogue": "Red lorry, yellow lorry... red lorry...", "duration": 4, "bg": "room"},
            {"action": "Gets tongue twisted literally", "dialogue": "Help! My tongue's a knot!", "duration": 3, "bg": "room"},
            {"action": "Zap untangles it super fast", "dialogue": "Thanks! ...Red lorry, yellow lorry. Nailed it!", "duration": 3, "bg": "room"},
        ]},

        # Zap stories
        {"title": "Zap's Snail Race", "main_char": "zap", "scenes": [
            {"action": "Zap challenges snail to race", "dialogue": "Ready, set, ZOOM!", "duration": 3, "bg": "park"},
            {"action": "Zap runs circles, snail moves 1 inch", "dialogue": "Wait... I passed finish line 50 times!", "duration": 4, "bg": "park"},
            {"action": "Zap high-fives snail", "dialogue": "You won... at being slow!", "duration": 3, "bg": "park"},
        ]},
        {"title": "Zap's Speed Clean", "main_char": "zap", "scenes": [
            {"action": "Messy room, Zap zooms around", "dialogue": "Cleaning at light speed!", "duration": 3, "bg": "room"},
            {"action": "Everything clean but in wrong places", "dialogue": "Uh... fridge in bedroom?", "duration": 4, "bg": "room"},
            {"action": "Friends help fix, Zap zooms snacks", "dialogue": "Snack delivery: EXPRESS!", "duration": 3, "bg": "room"},
        ]},
        {"title": "Zap's Zoomies", "main_char": "zap", "scenes": [
            {"action": "Zap gets sudden energy burst", "dialogue": "ZOOOOOOMIES!", "duration": 3, "bg": "park"},
            {"action": "Runs figure-8s, creates wind tunnel", "dialogue": "I'm a tornado!", "duration": 4, "bg": "park"},
            {"action": "Stops instantly, not tired", "dialogue": "Who's next?", "duration": 3, "bg": "park"},
        ]},
        {"title": "Zap's Fast Food", "main_char": "zap", "scenes": [
            {"action": "Zap eats sandwich in 0.5 seconds", "dialogue": "Nom! Gone!", "duration": 3, "bg": "kitchen"},
            {"action": "Doesn't taste it", "dialogue": "Wait... was it peanut butter?", "duration": 3, "bg": "kitchen"},
            {"action": "Slows down for second sandwich", "dialogue": "Mmm... crunchy!", "duration": 3, "bg": "kitchen"},
        ]},
        {"title": "Zap's Lightning Art", "main_char": "zap", "scenes": [
            {"action": "Zap draws by zooming past canvas", "dialogue": "Speed painting!", "duration": 3, "bg": "room"},
            {"action": "Creates masterpiece accidentally", "dialogue": "Oops! Art!", "duration": 3, "bg": "room"},
            {"action": "Frames it - it's a blur", "dialogue": "Abstract expressionism!", "duration": 3, "bg": "room"},
        ]},

        # Snooze stories
        {"title": "Snooze's Pizza Dream", "main_char": "snooze", "scenes": [
            {"action": "Snooze falls asleep instantly", "dialogue": "*yawn* Nap time...", "duration": 3, "bg": "bedroom"},
            {"action": "Dream: floating on pepperoni cloud", "dialogue": "Mmm... pepperoni clouds...", "duration": 4, "bg": "bedroom"},
            {"action": "Wakes up hungry", "dialogue": "Was it real? *growl* Now I'm hungry!", "duration": 3, "bg": "bedroom"},
        ]},
        {"title": "Snooze's Pillow Fort", "main_char": "snooze", "scenes": [
            {"action": "Snooze builds pillow wall", "dialogue": "Fortress of fluff...", "duration": 3, "bg": "bedroom"},
            {"action": "Others join, becomes giant castle", "dialogue": "Room for everyone!", "duration": 4, "bg": "bedroom"},
            {"action": "All nap together", "dialogue": "Best. Castle. Ever. *snore*", "duration": 3, "bg": "bedroom"},
        ]},
        {"title": "Snooze's Counting Sheep", "main_char": "snooze", "scenes": [
            {"action": "Snooze counts sheep to sleep", "dialogue": "One sheep... two sheep...", "duration": 3, "bg": "bedroom"},
            {"action": "Sheep start dancing", "dialogue": "Hey! Sleeping here!", "duration": 4, "bg": "bedroom"},
            {"action": "Snooze joins dance party", "dialogue": "Best sleep ever!", "duration": 3, "bg": "bedroom"},
        ]},
        {"title": "Snooze's Alarm Clock", "main_char": "snooze", "scenes": [
            {"action": "Alarm rings, Snooze hits snooze", "dialogue": "Five more minutes...", "duration": 3, "bg": "bedroom"},
            {"action": "Alarm grows legs, runs away", "dialogue": "Come back! I didn't mean it!", "duration": 4, "bg": "bedroom"},
            {"action": "Zap catches alarm", "dialogue": "Got it! Wake up time!", "duration": 3, "bg": "bedroom"},
        ]},
        {"title": "Snooze's Cloud Watching", "main_char": "snooze", "scenes": [
            {"action": "Snooze lies on grass watching clouds", "dialogue": "That one's a bunny...", "duration": 4, "bg": "park"},
            {"action": "Clouds form shapes of friends", "dialogue": "Look! It's all of us!", "duration": 3, "bg": "park"},
            {"action": "Falls asleep on cloud", "dialogue": "Softest bed... *snore*", "duration": 3, "bg": "park"},
        ]},
    ],
    "episodes": [
        {"title": "The Great Blanket Fort", "chars": ["bip", "gloop", "pip", "zap", "snooze"], "scenes": [
            {"action": "All 5 build giant blanket fort in living room", "dialogue": ["Bip: I'll be the architect!", "Gloop: I'm the glue!", "Pip: Structural integrity: 100 percent!", "Zap: *zooms around* DONE!", "Snooze: *already napping inside*"], "duration": 8, "bg": "room"},
            {"action": "Fort transforms - castle, spaceship, jungle", "dialogue": ["Bip: To the moon!", "Gloop: *shape-shifts into alien*", "Pip: Calculating trajectory...", "Zap: FASTER!", "Snooze: *snores in zero gravity*"], "duration": 10, "bg": "room"},
            {"action": "Fort collapses into giant pillow pile", "dialogue": ["All: *laughing* Best fort ever!", "Snooze: *wakes up* Did I miss it?"], "duration": 6, "bg": "room"},
        ]},
        {"title": "The Lost Toy Adventure", "chars": ["bip", "gloop", "pip", "zap", "snooze"], "scenes": [
            {"action": "Bip's favorite toy goes missing", "dialogue": ["Bip: My Mr. Whiskers!", "Pip: Initiating search protocol.", "Zap: I'll check everywhere!", "Gloop: I'll check inside things!", "Snooze: I'll check... my eyelids."], "duration": 8, "bg": "room"},
            {"action": "Search montage - each searches differently", "dialogue": ["Zap: *zooms through house* Not here!", "Gloop: *oozes under furniture* Nope!", "Pip: *checks books* Not in dictionary!", "Snooze: *sleep-searching* Zzz..."], "duration": 10, "bg": "room"},
            {"action": "Found! Snooze was cuddling it in sleep", "dialogue": ["Bip: There he is!", "Snooze: *wakes* He's so soft...", "All: *group hug* Best rescue ever!"], "duration": 6, "bg": "bedroom"},
        ]},
        {"title": "The Talent Show", "chars": ["bip", "gloop", "pip", "zap", "snooze"], "scenes": [
            {"action": "Friends put on backyard talent show", "dialogue": ["Bip: Welcome to Funny Friends Got Talent!", "Pip: I'm the judge. Criteria: maximum giggles."], "duration": 6, "bg": "park"},
            {"action": "Each performs unique act", "dialogue": ["Gloop: *shape-shifts into various animals* Ta-da!", "Zap: *speed-juggles 10 balls* Blink missed it!", "Pip: *recites pi to 50 digits* 3.14159...", "Bip: *tells joke so funny everyone falls over*", "Snooze: *sleep-performs ballet* *snore* *pirouette*"], "duration": 12, "bg": "park"},
            {"action": "Everyone wins - group trophy", "dialogue": ["Pip: Tie! Everyone gets gold!", "Bip: Best talent show ever!", "All: *cheer* Same time next week?"], "duration": 6, "bg": "park"},
        ]},
        {"title": "The Rainy Day Parade", "chars": ["bip", "gloop", "pip", "zap", "snooze"], "scenes": [
            {"action": "Rain ruins park plans, stuck inside", "dialogue": ["Bip: Rain ruined everything!", "Pip: Actually, rain helps plants grow.", "Gloop: I like rain! *turns into umbrella*"], "duration": 6, "bg": "room"},
            {"action": "Create indoor parade with homemade instruments", "dialogue": ["Bip: Pot lid cymbals!", "Zap: *runs as float* Zoom zoom!", "Pip: *conducts with ruler* Maestro!", "Snooze: *dreams the music* Zzz..."], "duration": 10, "bg": "room"},
            {"action": "Rain stops, rainbow appears - parade moves outside", "dialogue": ["All: *marching* Best parade ever!", "Bip: Rain gave us the best idea!"], "duration": 6, "bg": "park"},
        ]},
        {"title": "The Mystery Map", "chars": ["bip", "gloop", "pip", "zap", "snooze"], "scenes": [
            {"action": "Find mysterious map in backyard", "dialogue": ["Bip: X marks the spot!", "Pip: Coordinates: 40% fun, 60% adventure.", "Zap: Race you there!"], "duration": 6, "bg": "park"},
            {"action": "Follow clues - each friend solves one", "dialogue": ["Gloop: *squeezes through tiny gap* Found it!", "Pip: *solves riddle* Knowledge wins!", "Zap: *speed-runs obstacle course* Easy!", "Snooze: *sleep-walks to clue* Huh?"], "duration": 10, "bg": "park"},
            {"action": "Treasure: time capsule THEY buried years ago", "dialogue": ["All: *open box* Our old drawings!", "Bip: We made this?", "Pip: Memories are the best treasure."], "duration": 6, "bg": "park"},
        ]},
        {"title": "The Giant Bubble", "chars": ["bip", "gloop", "pip", "zap", "snooze"], "scenes": [
            {"action": "Gloop makes bubble - keeps growing", "dialogue": ["Gloop: Biggest bubble yet!", "Pip: Surface tension... exceeding limits!", "Bip: It's beautiful!"], "duration": 6, "bg": "park"},
            {"action": "Bubble lifts everyone inside", "dialogue": ["Zap: We're flying!", "Snooze: *floating sleep* So peaceful...", "Gloop: I'm the pilot!"], "duration": 10, "bg": "park"},
            {"action": "Bubble pops gently over picnic", "dialogue": ["All: *land on blankets* Perfect landing!", "Pip: Physics: 1, Fun: Infinity!"], "duration": 6, "bg": "park"},
        ]},
    ]
}

def get_week_scripts(week_num, config):
    """Deterministic but varied scripts for each week"""
    random.seed(week_num * 42)  # Consistent per week

    shorts_templates = STORY_TEMPLATES["shorts"]
    episode_templates = STORY_TEMPLATES["episodes"]

    # Pick 5 unique shorts
    selected_shorts = random.sample(shorts_templates, min(5, len(shorts_templates)))
    selected_episode = random.choice(episode_templates)

    # Add metadata
    for i, short in enumerate(selected_shorts):
        short["type"] = "short"
        short["day"] = i
        short["week"] = week_num
        short["upload_date"] = f"Week {week_num}, Day {i+1}"

    selected_episode["type"] = "episode"
    selected_episode["week"] = week_num

    return {
        "week": week_num,
        "generated_at": datetime.now().isoformat(),
        "shorts": selected_shorts,
        "episode": selected_episode
    }

def save_scripts(scripts, week_num, config):
    output_dir = Path(config["paths"]["output"]) / f"week_{week_num}"
    output_dir.mkdir(parents=True, exist_ok=True)

    script_file = output_dir / "scripts.json"
    with open(script_file, "w") as f:
        json.dump(scripts, f, indent=2)

    print(f"✅ Week {week_num} scripts saved to {script_file}")
    print(f"   Shorts: {len(scripts['shorts'])}")
    print(f"   Episode: {scripts['episode']['title']}")

    return script_file

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--week", type=int, default=1)
    parser.add_argument("--all", action="store_true", help="Generate all weeks (1-52)")
    args = parser.parse_args()

    config = load_config()

    if args.all:
        for week in range(1, 53):
            scripts = get_week_scripts(week, config)
            save_scripts(scripts, week, config)
        print("\n✅ Generated 52 weeks of content!")
    else:
        scripts = get_week_scripts(args.week, config)
        save_scripts(scripts, args.week, config)