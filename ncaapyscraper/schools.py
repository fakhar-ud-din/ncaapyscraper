import csv
import os
import re

from ncaapyscraper.selectors import (
    roster_table_css_v1,
    roster_table_css_v2,
    schedule_css_v1,
    schedule_css_v2,
    schedule_css_v3,
)


SCHOOLS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schools.csv')

# Short names people actually type
ALIASES = {
    'navy': 'us_naval_academy',
    'army': 'us_military_academy',
    'air_force': 'us_air_force_academy',
    'georgia_tech': 'georgia_institute_of_technology',
    'mit': 'massachusetts_institute_of_technology',
    'caltech': 'california_institute_of_technology',
    'rit': 'rochester_institute_of_technology',
    'rpi': 'rensselaer_polytechnic_institute',
    'njit': 'new_jersey_institute_of_technology',
    'cal_poly': 'california_polytechnic_state',
    'uconn': 'connecticut',
    'umass': 'massachusetts_amherst',
    'unc': 'north_carolina',
    'penn': 'pennsylvania',
    'smu': 'southern_methodist',
    'unlv': 'nevada_las_vegas',
    'utep': 'texas_el_paso',
    'utsa': 'texas_san_antonio',
    'uab': 'alabama_birmingham',
    'usf': 'south_florida',
    'fiu': 'florida_international',
    'fau': 'florida_atlantic',
    'vcu': 'virginia_commonwealth',
    'miami': 'miami_florida',
    'miami_ohio': 'miami_university_ohio',
    'southern_miss': 'southern_mississippi',
}

CONFERENCES = {
    'acc': 'Atlantic Coast Conference',
    'big10': 'Big Ten Conference',
    'bigten': 'Big Ten Conference',
    'big12': 'Big 12 Conference',
    'sec': 'Southeastern Conference',
    'pac12': 'Pac-12 Conference',
    'aac': 'American Conference',
    'american': 'American Conference',
    'mwc': 'Mountain West Conference',
    'cusa': 'Conference USA',
    'mac': 'Mid-American Conference',
    'sunbelt': 'Sun Belt Conference',
    'ivy': 'The Ivy League',
    'a10': 'Atlantic 10 Conference',
    'bigeast': 'BIG EAST Conference',
    'wcc': 'West Coast Conference',
    'mvc': 'Missouri Valley Conference',
    'bigsky': 'Big Sky Conference',
    'bigsouth': 'Big South Conference',
    'bigwest': 'Big West Conference',
    'caa': 'Coastal Athletic Association',
    'asun': 'Atlantic Sun Conference',
    'socon': 'Southern Conference',
    'swac': 'Southwestern Athletic Conf.',
    'meac': 'Mid-Eastern Athletic Conf.',
    'nec': 'Northeast Conference',
    'ovc': 'Ohio Valley Conference',
    'summit': 'The Summit League',
    'horizon': 'Horizon League',
    'patriot': 'Patriot League',
    'southland': 'Southland Conference',
    'uac': 'United Athletic Conference',
    'maac': 'Metro Conference',
    'americaeast': 'America East Conference',
}

# The WordPress sites each have their own markup
WORDPRESS_SELECTORS = {
    'arkansas': {'roster_css': roster_table_css_v2, 'schedule_css': schedule_css_v3},
    'kentucky': {'roster_css': roster_table_css_v1, 'schedule_css': schedule_css_v1},
    'south_carolina': {'roster_css': roster_table_css_v1, 'schedule_css': schedule_css_v2},
}


def load_schools():
    schools = {}
    with open(SCHOOLS_FILE, encoding='utf-8') as schools_file:
        for row in csv.DictReader(schools_file):
            row['division'] = int(row['division'] or 0)
            schools[row['key']] = {**row, **WORDPRESS_SELECTORS.get(row['key'], {})}

    return schools


SCHOOLS = load_schools()


def bare_site(site):
    return re.sub(r'^(https?://)?(www\.)?', '', (site or '').lower()).strip('/')


def find_school(key_or_site):
    "duke"
    "goduke.com"
    "https://www.goduke.com/"
    # A school that isn't in the csv yet, {'name': ..., 'site': ..., 'platform': ...} is enough
    if isinstance(key_or_site, dict):
        defaults = {'key': re.sub(r'[^a-z0-9]+', '_', bare_site(key_or_site.get('site')).split('.')[0]), 'conference': '', 'division': 0, 'subdivision': '', 'state': ''}
        return {**defaults, 'name': key_or_site.get('site'), **key_or_site}

    value = (key_or_site or '').lower().strip()
    value = ALIASES.get(value, value)
    if value in SCHOOLS:
        return SCHOOLS[value]

    site = bare_site(value)
    for school in SCHOOLS.values():
        if bare_site(school['site']) == site:
            return school

    return None


def conference_name(conference):
    "sec"
    "big-ten"
    "Southeastern Conference"
    value = re.sub(r'[^a-z0-9]', '', (conference or '').lower())
    if value in CONFERENCES:
        return CONFERENCES[value]

    names = sorted({school['conference'] for school in SCHOOLS.values()})
    exact = [name for name in names if re.sub(r'[^a-z0-9]', '', name.lower()) == value]
    partial = [name for name in names if value and value in re.sub(r'[^a-z0-9]', '', name.lower())]
    return (exact or partial or [None])[0]


def pick_schools(conference=None, division=None):
    "division 1, 2, 3, fbs or fcs"
    name = conference and conference_name(conference)
    if conference and not name:
        return []

    division = str(division or '').lower()
    picked = []
    for key, school in SCHOOLS.items():
        if name and school['conference'] != name:
            continue

        if division in ('1', '2', '3') and school['division'] != int(division):
            continue

        if division in ('fbs', 'fcs') and school['subdivision'].lower() != division:
            continue

        picked.append(key)

    return picked
