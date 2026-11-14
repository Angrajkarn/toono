#!/usr/bin/env python3
"""Get current week number from config.yaml"""
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
    print(f'week={week}')
except Exception as e:
    print(f'ERROR: {e}', file=sys.stderr)
    sys.exit(1)