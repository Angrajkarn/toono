#!/usr/bin/env python3
"""Get current week number and day type from config.yaml"""
import datetime
import yaml
import sys

try:
    with open('config.yaml', 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f) or {}
    start_str = cfg.get('automation', {}).get('start_date', '2025-01-06')
    start = datetime.datetime.strptime(start_str, '%Y-%m-%d')
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    week = ((now - start).days // 7) + 1
    week = max(1, min(week, 52))
    day_of_week = now.weekday()
    if day_of_week <= 4:
        content_type = 'short'
        day_index = day_of_week
    elif day_of_week == 5:
        content_type = 'episode'
        day_index = 0
    else:
        content_type = 'none'
        day_index = -1
    print(f'week={week}')
    print(f'day_index={day_index}')
    print(f'content_type={content_type}')
    print(f'day_of_week={day_of_week}')
except Exception as e:
    print(f'ERROR: {e}', file=sys.stderr)
    sys.exit(1)