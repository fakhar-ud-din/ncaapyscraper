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

NCAA_COM = 'https://www.ncaa.com'
NCAA_GRAPHQL = 'https://sdataprod.ncaa.com/'

# ncaa.com slug, scoreboard code and box score query per sport. "national" sports have one
# championship for D1 and D2, ncaa.com still calls it d1 but its division id is 0
NCAA_SPORTS = {
    'football': {'slug': 'football', 'code': 'MFB', 'boxscore': 'Football', 'divisions': ['fbs', 'fcs', 'd2', 'd3']},
    'mens-basketball': {'slug': 'basketball-men', 'code': 'MBB', 'boxscore': 'Basketball', 'divisions': ['d1', 'd2', 'd3']},
    'womens-basketball': {'slug': 'basketball-women', 'code': 'WBB', 'boxscore': 'Basketball', 'divisions': ['d1', 'd2', 'd3']},
    'baseball': {'slug': 'baseball', 'code': 'MBA', 'boxscore': 'Baseball', 'divisions': ['d1', 'd2', 'd3']},
    'softball': {'slug': 'softball', 'code': 'WSB', 'boxscore': 'Softball', 'divisions': ['d1', 'd2', 'd3']},
    'womens-volleyball': {'slug': 'volleyball-women', 'code': 'WVB', 'boxscore': 'Volleyball', 'divisions': ['d1', 'd2', 'd3']},
    'mens-volleyball': {'slug': 'volleyball-men', 'code': 'MVB', 'boxscore': 'Volleyball', 'divisions': ['d1', 'd3'], 'national': True},
    'beach-volleyball': {'slug': 'beach-volleyball', 'code': 'WSV', 'boxscore': None, 'divisions': ['d1'], 'national': True},
    'mens-soccer': {'slug': 'soccer-men', 'code': 'MSO', 'boxscore': 'Soccer', 'divisions': ['d1', 'd2', 'd3']},
    'womens-soccer': {'slug': 'soccer-women', 'code': 'WSO', 'boxscore': 'Soccer', 'divisions': ['d1', 'd2', 'd3']},
    'mens-ice-hockey': {'slug': 'icehockey-men', 'code': 'MIH', 'boxscore': 'Icehockey', 'divisions': ['d1', 'd3']},
    'womens-ice-hockey': {'slug': 'icehockey-women', 'code': 'WIH', 'boxscore': 'Icehockey', 'divisions': ['d1', 'd3'], 'national': True},
    'mens-lacrosse': {'slug': 'lacrosse-men', 'code': 'MLA', 'boxscore': 'Lacrosse', 'divisions': ['d1', 'd2', 'd3']},
    'womens-lacrosse': {'slug': 'lacrosse-women', 'code': 'WLA', 'boxscore': 'Lacrosse', 'divisions': ['d1', 'd2', 'd3']},
    'field-hockey': {'slug': 'fieldhockey', 'code': 'WFH', 'boxscore': 'Fieldhockey', 'divisions': ['d1', 'd2', 'd3']},
}

NCAA_SPORT_ALIASES = {
    'volleyball': 'womens-volleyball',
}

NCAA_DIVISIONS = {
    'd1': 1,
    'd2': 2,
    'd3': 3,
    'fbs': 11,
    'fcs': 12,
}

# Persisted GraphQL queries ncaa.com's own pages call. The hashes change when the site deploys,
# the client then picks up the new ones from the page
NCAA_QUERIES = {
    'GetContests_web': '4bcb5e6432fa9da365c0c19af01b1f9015cc7eb5c21e7af2dba308784a166df7',
    'NCAA_GetGamecenterBoxscoreBaseballById_web': '5e92118b2f424040aa96067aba6d34e882165aaf02e9e73cb9d69317066c6ae8',
    'NCAA_GetGamecenterBoxscoreBasketballById_web': '4a7fa26398db33de3ff51402a90eb5f25acef001cca28d239fe5361315d1419a',
    'NCAA_GetGamecenterBoxscoreFieldhockeyById_web': 'eff2e8b300974fd628e8718bfeb476e8d1897eb2a0fda7f8fdcae5b29ce2e54e',
    'NCAA_GetGamecenterBoxscoreFootballById_web': 'babb939def47c602a6e81af7aa3f6b35197fb1f1b1a2f2b081f3a3e4924be82e',
    'NCAA_GetGamecenterBoxscoreIcehockeyById_web': 'a4be206372277e685a002162f3caeecbfd9e61905835735d0ea9e48e336cddd4',
    'NCAA_GetGamecenterBoxscoreLacrosseById_web': 'dfd0e926e92e81c2917b8f4ae564fbdcd5c69cd0441a2a8095b6b09e4cee7c36',
    'NCAA_GetGamecenterBoxscoreSoccerById_web': 'c9070c4e5a76468a4025896df89f8a7b22be8275c54a22ff79619cbb27d63d7d',
    'NCAA_GetGamecenterBoxscoreSoftballById_web': '8fcd4071199071483be215ff66a2e3676f98563e26a7ff1ba113d56ce28a398d',
    'NCAA_GetGamecenterBoxscoreVolleyballById_web': '4320484382257c2a7ac3be318db2dee09a7fb74029448825c285d5dbdda365ae',
}

GAME_STATES = {
    'F': 'final',
    'I': 'live',
    'P': 'scheduled',
}

# Box score keys that describe the player, everything else is a stat
BOXSCORE_PLAYER_KEYS = ['firstName', 'lastName', 'number', 'position', 'category', '__typename']

STAT_HEADINGS = {
    'cl': 'player_class',
    'g': 'games',
    'gp': 'games',
}

# Rows with the same key are the same record, newer ones replace older ones when files are merged
GAME_KEY = ['game_id']
BOXSCORE_KEY = ['game_id', 'team_id', 'name', 'shirt_no']
