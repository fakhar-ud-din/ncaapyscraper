import re

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from w3lib.html import remove_tags, replace_entities

from ncaapyscraper.constants import *


def clean(list_or_str):
    if isinstance(list_or_str, list):
        return [clean(item) for item in list_or_str]

    if list_or_str is None:
        return None

    list_or_str = str(list_or_str).replace('\xa0', ' ')
    list_or_str = re.sub(r'\s+', ' ', list_or_str)
    return list_or_str.strip()


def clean_value(value):
    value = clean(value) or ''
    if value.lower() in EMPTY_VALUES:
        return ''

    return value


def clean_bio(html):
    if not html:
        return ''

    html = re.sub(r'<(br|/p|/li|/h\d)[^>]*>', ' ', html)
    return clean(replace_entities(remove_tags(html)))


def sports_gender(sports_name):
    "Men's Basketball"
    sports_name = clean(sports_name) or ''
    gender = re.findall(r"^(Men|Women)[’']?s?\b", sports_name, re.I)
    return gender and GENDER_MAP[gender[0].lower()] or SPORT_GENDERS.get(sports_name.lower(), '')


def sport_key(text):
    "Men's Swimming & Diving"
    text = re.sub(r"[’']", '', (text or '').lower().replace('&', ' and '))
    return re.sub(r'[^a-z0-9]+', '-', text).strip('-')


def split_arg(value):
    "football,mens-basketball"
    if not value:
        return []

    values = value if isinstance(value, (list, tuple)) else [value]
    return [clean(part) for item in values for part in str(item).split(',') if clean(part)]


def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', (text or '').lower()).strip('-')


def snake_case(text):
    "rushingYards"
    "Rush TD"
    "PREVIOUS RANKING"
    text = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', clean(text) or '')
    return re.sub(r'[^a-z0-9]+', '_', text.lower()).strip('_')


def to_number(value):
    "1,729"
    "0.944"
    ".000"
    if not isinstance(value, str):
        return value

    text = value.replace(',', '').strip()
    if re.fullmatch(r'-?\d+', text):
        return int(text)

    if re.fullmatch(r'-?\d*\.\d+', text):
        return float(text)

    return clean(value) or None


def format_height(feet, inches):
    if not feet:
        return ''

    return f'{feet}-{inches or 0}'


def normalize_height(height):
    "6'0\""
    "6-2"
    height = clean(height) or ''
    match = re.match(r"^(\d)\s*['’-]\s*(\d{1,2})", height)
    return match and f'{match.group(1)}-{match.group(2)}' or height


def format_weight(weight):
    "244 lbs."
    weight = re.findall(r'(\d+)', str(weight or ''))
    return weight and weight[0] or ''


def format_score(score):
    "37.0000"
    if score in (None, ''):
        return ''

    try:
        return ('%f' % float(score)).rstrip('0').rstrip('.')
    except ValueError:
        return clean(score)


def is_time(date_time):
    date_time = (date_time or '').lower()
    time_res = [rf'\d+\s*{re.escape(time_f)}' for time_f in TIME_SLUGS[1:]]

    if 'noon' in date_time or 'tba' in date_time:
        return True

    return any(re.search(time_re, date_time) for time_re in time_res)


def format_time(time_text):
    "7 p.m."
    "12:45 pm"
    "Noon"
    time_text = clean(time_text) or ''
    if 'noon' in time_text.lower():
        return '12:00 PM'

    match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*([ap])\.?\s*m\b\.?', time_text, re.I)
    if not match:
        return time_text

    hour, minute, meridiem = match.groups()
    return f"{int(hour)}:{minute or '00'} {meridiem.upper()}M"


def split_result(result, score=''):
    "W, 31-14"
    "L 7-35"
    text = clean(f'{result or ""} {score or ""}')
    match = re.match(r'^(W|L|T)\b[\s,]*(.*)$', text)
    if not match:
        return '', text

    outcome, score = match.group(1), clean(match.group(2))

    # Team score goes first, some sites always put the winner first
    scores = re.match(r'^(\d+)\s*-\s*(\d+)(.*)$', score)
    if scores:
        first, second, rest = int(scores.group(1)), int(scores.group(2)), scores.group(3)
        if (outcome == 'W' and first < second) or (outcome == 'L' and first > second):
            first, second = second, first
        score = clean(f'{first}-{second}{rest}')

    return outcome, score


def clean_opponent(opponent):
    "at #20 Utah"
    "vs. Youngstown State"
    opponent = re.sub(r'^(at|vs\.?)\s+', '', clean(opponent) or '', flags=re.I)
    return clean(re.sub(r'^#\d+\s+', '', opponent))


def parse_month_day(date_text):
    "Sat. Apr 18"
    "Sat Sep 5"
    "Sep. 5"
    for month, day in re.findall(r'([A-Za-z]{3})[a-z]*\.?\s+(\d{1,2})\b', date_text or ''):
        if month.lower() in MONTHS:
            return MONTHS.index(month.lower()) + 1, int(day)

    return None, None


def season_dates(month_days, start_year):
    # Schedules run in order, so a smaller month means the season crossed into a new year
    dates = []
    year, previous = start_year, 0

    for month, day in month_days:
        if not month or not year:
            dates.append('')
            continue

        if month < previous:
            year += 1
        previous = month

        dates.append(f'{year}-{month:02d}-{day:02d}')

    return dates


def season_year(season):
    year = re.findall(r'(\d{4})', season or '')
    return year and int(year[0]) or None


def to_utc(date_time):
    if not date_time:
        return None

    parsed = datetime.fromisoformat(re.sub(r'\.\d+', '', date_time).replace('Z', '+00:00'))
    if not parsed.tzinfo:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def to_local(date_time, time_zone):
    utc = to_utc(date_time)
    return utc and utc.astimezone(ZoneInfo(time_zone or DEFAULT_TIMEZONE)) or None


def utc_text(date_time):
    utc = to_utc(date_time)
    return utc and utc.strftime('%Y-%m-%dT%H:%M:%SZ') or ''
