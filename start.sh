#!/bin/bash
# ==========================================
#  🎬 CARTOON CHANNEL - MAC/LINUX LAUNCHER
# ==========================================
# Run: ./start.sh
# Make executable: chmod +x start.sh

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

show_menu() {
    clear
    echo -e "${BLUE}==========================================${NC}"
    echo -e "${BLUE}  🎬 FUNNY FRIENDS CARTOON CHANNEL${NC}"
    echo -e "${BLUE}==========================================${NC}"
    echo
    echo -e "${GREEN}Choose an option:${NC}"
    echo
    echo "  [1] FIRST TIME SETUP (run once)"
    echo "  [2] RUN THIS WEEK NOW"
    echo "  [3] RUN SPECIFIC WEEK"
    echo "  [4] SETUP CRON JOB (auto forever)"
    echo "  [5] TEST PIPELINE (quick verify)"
    echo "  [6] YOUTUBE AUTHORIZATION"
    echo "  [0] EXIT"
    echo
}

run_setup() {
    echo -e "${YELLOW}🚀 Running first-time setup...${NC}"
    python run_pipeline.py --setup
    read -p "Press Enter to continue..."
}

run_current() {
    echo -e "${YELLOW}🎬 Running current week...${NC}"
    python run_pipeline.py
    read -p "Press Enter to continue..."
}

run_week() {
    read -p "Enter week number (1-52): " week
    echo -e "${YELLOW}🎬 Running week $week...${NC}"
    python run_pipeline.py --week "$week"
    read -p "Press Enter to continue..."
}

setup_cron() {
    echo -e "${YELLOW}⚙️ Setting up cron job...${NC}"
    PROJECT_PATH=$(pwd)
    PYTHON_PATH=$(which python3)

    # Add to crontab (runs every Monday at 10:00)
    (crontab -l 2>/dev/null | grep -v "cartoon_channel"; echo "0 10 * * 1 cd $PROJECT_PATH && $PYTHON_PATH run_pipeline.py >> $PROJECT_PATH/logs/cron.log 2>&1") | crontab -

    echo -e "${GREEN}✅ Cron job added!${NC}"
    echo "Runs every Monday at 10:00 AM"
    echo "Logs: $PROJECT_PATH/logs/cron.log"
    read -p "Press Enter to continue..."
}

run_test() {
    echo -e "${YELLOW}🧪 Testing pipeline...${NC}"
    python test_pipeline.py
    read -p "Press Enter to continue..."
}

youtube_auth() {
    echo -e "${YELLOW}🔐 Authorizing YouTube API...${NC}"
    python upload.py --auth
    read -p "Press Enter to continue..."
}

# Main loop
while true; do
    show_menu
    read -p "Enter choice (0-6): " choice

    case $choice in
        1) run_setup ;;
        2) run_current ;;
        3) run_week ;;
        4) setup_cron ;;
        5) run_test ;;
        6) youtube_auth ;;
        0) echo -e "${GREEN}👋 Goodbye!${NC}"; exit 0 ;;
        *) echo -e "${RED}Invalid choice${NC}"; sleep 1 ;;
    esac
done