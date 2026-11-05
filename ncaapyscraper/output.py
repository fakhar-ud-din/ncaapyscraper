import json
import os

from datetime import datetime, timezone

from ncaapyscraper.constants import PLAYER_FIELDS, COACH_FIELDS, SCHEDULE_FIELDS
from ncaapyscraper.items import TeamScheduleItem


DATA_KEYS = {
    'players': 'players',
    'coaches': 'coaches',
    'schedules': 'schedule',
}


def school_result(school, items, data, bios=True):
    "Groups the scraped items by sport, the same shape the json files have"
    sports = {}
    for item in items:
        sport = sports.setdefault(item.get('sport') or '', {
            'sport': item.get('sport') or None,
            'gender': item.get('sport_gender') or None,
            'season': item.get('season') or None,
            'players': [],
            'coaches': [],
            'schedule': [],
        })
        sport['season'] = sport['season'] or item.get('season') or None

        if isinstance(item, TeamScheduleItem):
            sport['schedule'].append(row(item, SCHEDULE_FIELDS))
        elif item.get('is_coach'):
            sport['coaches'].append(row(item, COACH_FIELDS, bios))
        else:
            sport['players'].append(row(item, PLAYER_FIELDS, bios))

    sports = sorted(sports.values(), key=lambda sport: sport['sport'] or '')
    for sport in sports:
        for data_type, key in DATA_KEYS.items():
            if data_type not in data:
                sport.pop(key)

    return {
        'key': school['key'],
        'school': school['name'],
        'conference': school.get('conference') or None,
        'division': school.get('division') or None,
        'subdivision': school.get('subdivision') or None,
        'state': school.get('state') or None,
        'site': f"https://{school['site']}",
        'platform': school['platform'],
        'scraped_at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'sports': sports,
    }


def row(item, fields, bios=True):
    row = {}
    for field in fields:
        if field == 'bio' and not bios:
            continue

        value = item.get(field)

        if value in ('', None):
            value = None
        elif field == 'weight' and str(value).isdigit():
            value = int(value)
        elif field == 'is_conference':
            value = bool(int(value))

        row[field] = value

    return row


def summary(result):
    sports = result['sports']
    return {
        'sports': len(sports),
        'players': sum(len(sport.get('players') or []) for sport in sports),
        'coaches': sum(len(sport.get('coaches') or []) for sport in sports),
        'games': sum(len(sport.get('schedule') or []) for sport in sports),
    }


def write_result(result, output_dir='output', indent=2):
    os.makedirs(output_dir, exist_ok=True)

    path = os.path.join(output_dir, f"{result['key']}.json")
    with open(path, 'w', encoding='utf-8') as output_file:
        json.dump(result, output_file, indent=indent, ensure_ascii=False)

    return path
