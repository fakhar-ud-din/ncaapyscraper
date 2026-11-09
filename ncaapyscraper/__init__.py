"""Rosters, coaches and schedules from college athletics websites, scores and stats from ncaa.com.

    import ncaapyscraper as nps

    nps.get_roster("duke", "football")
    nps.get_schedule("alabama", "mens-basketball")
    nps.get_school("navy", sports=["football"])
    nps.get_scoreboard("football", week=10)
    nps.get_boxscore(6640609)
"""

__version__ = '0.2.0'

from ncaapyscraper.api import (
    fetch_school,
    fetch_schools,
    fetch_roster,
    fetch_coaches,
    fetch_schedule,
    fetch_scoreboard,
    fetch_boxscore,
    fetch_rankings,
    fetch_standings,
    fetch_stat_list,
    fetch_stats,
    fetch_games,
    get_school,
    get_roster,
    get_coaches,
    get_schedule,
    get_scoreboard,
    get_boxscore,
    get_rankings,
    get_standings,
    get_stat_list,
    get_stats,
    list_schools,
)
from ncaapyscraper.schools import find_school


__all__ = [
    'fetch_school',
    'fetch_schools',
    'fetch_roster',
    'fetch_coaches',
    'fetch_schedule',
    'fetch_scoreboard',
    'fetch_boxscore',
    'fetch_rankings',
    'fetch_standings',
    'fetch_stat_list',
    'fetch_stats',
    'fetch_games',
    'get_school',
    'get_roster',
    'get_coaches',
    'get_schedule',
    'get_scoreboard',
    'get_boxscore',
    'get_rankings',
    'get_standings',
    'get_stat_list',
    'get_stats',
    'list_schools',
    'find_school',
]
