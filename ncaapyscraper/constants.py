MONTHS = [
    'jan',
    'feb',
    'mar',
    'apr',
    'may',
    'jun',
    'jul',
    'aug',
    'sep',
    'oct',
    'nov',
    'dec',
]

TIME_SLUGS = [
    'noon', 'am', 'pm', 'p.m', 'a.m'
]

DEFAULT_TIMEZONE = 'America/New_York'

GENDER_MAP = {
    'm': 'men',
    'men': 'men',
    'mens': 'men',
    'male': 'men',
    'f': 'women',
    'w': 'women',
    'women': 'women',
    'womens': 'women',
    'female': 'women',
}

# Sports that don't say men's or women's in the name
SPORT_GENDERS = {
    'football': 'men',
    'baseball': 'men',
    'softball': 'women',
    'field hockey': 'women',
    'volleyball': 'women',
    'beach volleyball': 'women',
}

VENUE_MAP = {
    'H': 'home',
    'A': 'away',
    'N': 'neutral',
}

RESULT_MAP = {
    'W': 'W',
    'L': 'L',
    'T': 'T',
    'win': 'W',
    'loss': 'L',
    'tie': 'T',
}

TABLE_HEADINGS = {
    'number': 'shirt_no',
    'num': 'shirt_no',
    'no': 'shirt_no',
    '#': 'shirt_no',
    'name': 'name',
    'full name': 'name',
    'position': 'position',
    'pos': 'position',
    'events': 'position',
    'height': 'height',
    'ht': 'height',
    'weight': 'weight',
    'wt': 'weight',
    'class': 'player_class',
    'cl': 'player_class',
    'yr': 'player_class',
    'year': 'player_class',
    'academic year': 'player_class',
    'eligibility': 'player_class',
    'hometown': 'hometown',
    'high school': 'highschool',
    'previous school': 'previous_school',
    'last school': 'highschool',
    'high school/previous school': 'highschool/previous_school',
    'hometown/high school': 'hometown/highschool',
    'major': 'major',
}

EMPTY_VALUES = ['-', '--', 'n/a']

META_KEYS = ['sports_name', 'slug', 'gender', 'season', 'timezone']

DATA_TYPES = ['players', 'coaches', 'schedules']

PLAYER_FIELDS = [
    'name',
    'first_name',
    'last_name',
    'shirt_no',
    'position',
    'height',
    'weight',
    'player_class',
    'hometown',
    'highschool',
    'previous_school',
    'major',
    'gender',
    'image_url',
    'profile_url',
    'bio',
]

COACH_FIELDS = [
    'name',
    'first_name',
    'last_name',
    'title',
    'image_url',
    'profile_url',
    'bio',
]

SCHEDULE_FIELDS = [
    'date',
    'time',
    'datetime_utc',
    'opponent',
    'home_away',
    'location',
    'venue',
    'is_conference',
    'result',
    'score',
    'tournament',
    'tv',
    'image_url',
]
