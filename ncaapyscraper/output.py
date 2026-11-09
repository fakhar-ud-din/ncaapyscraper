import csv
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


def flatten(result, key):
    "One flat list across sports, handy for pandas"
    rows = []
    for sport in result['sports']:
        for record in sport.get(key) or []:
            rows.append({'school': result['school'], 'sport': sport['sport'], 'season': sport['season'], **record})

    return rows


def school_tables(results):
    "Players, coaches and schedules of many schools, one flat table each"
    tables = {data_type: [] for data_type in DATA_KEYS}

    for result in results:
        school = {
            'school_key': result['key'],
            'school': result['school'],
            'conference': result.get('conference'),
            'division': result.get('division'),
            'subdivision': result.get('subdivision'),
        }
        for data_type, key in DATA_KEYS.items():
            tables[data_type] += [{**school, **record} for record in flatten(result, key)]

    return tables


def load_pyarrow():
    try:
        import pyarrow
        import pyarrow.parquet
    except ImportError:
        raise ImportError('Parquet files need pyarrow, pip install "ncaapyscraper[parquet]"') from None

    return pyarrow


def write_parquet(rows, path):
    pyarrow = load_pyarrow()
    columns = list(dict.fromkeys(field for row in rows for field in row))

    arrays = []
    for column in columns:
        values = [row.get(column) for row in rows]
        try:
            arrays.append(pyarrow.array(values))
        except (pyarrow.ArrowInvalid, pyarrow.ArrowTypeError):
            # A number in one row and text in another (rank 5 and "T-5"), the column stays text
            arrays.append(pyarrow.array([None if value is None else str(value) for value in values]))

    pyarrow.parquet.write_table(pyarrow.table(arrays, names=columns), path)


def read_rows(path):
    extension = os.path.splitext(path)[1].lower()

    if extension == '.parquet':
        return load_pyarrow().parquet.read_table(path).to_pylist()

    with open(path, encoding='utf-8', newline='') as input_file:
        return list(csv.DictReader(input_file)) if extension == '.csv' else json.load(input_file)


def write_rows(rows, path, key=None):
    "json, csv or parquet by the file extension. With a key, rows already in the file are kept and updated"
    rows = list(rows)
    if key and os.path.exists(path):
        merged = {tuple(row.get(field) for field in key): row for row in read_rows(path) + rows}
        rows = list(merged.values())

    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    extension = os.path.splitext(path)[1].lower()

    if extension == '.parquet':
        write_parquet(rows, path)
    elif extension == '.csv':
        with open(path, 'w', encoding='utf-8', newline='') as output_file:
            writer = csv.DictWriter(output_file, list(dict.fromkeys(field for row in rows for field in row)))
            writer.writeheader()
            writer.writerows(rows)
    else:
        with open(path, 'w', encoding='utf-8') as output_file:
            json.dump(rows, output_file, indent=2, ensure_ascii=False)

    return len(rows)
