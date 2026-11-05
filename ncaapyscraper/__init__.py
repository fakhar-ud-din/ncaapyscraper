"""Rosters, coaches and schedules from college athletics websites.

    import ncaapyscraper as nps

    nps.get_roster("duke", "football")
    nps.get_schedule("alabama", "mens-basketball")
    nps.get_school("navy", sports=["football"])
"""

__version__ = '0.1.0'

from ncaapyscraper.api import (
    fetch_school,
    fetch_schools,
    fetch_roster,
    fetch_coaches,
    fetch_schedule,
    get_school,
    get_roster,
    get_coaches,
    get_schedule,
    list_schools,
)
from ncaapyscraper.schools import find_school


__all__ = [
    'fetch_school',
    'fetch_schools',
    'fetch_roster',
    'fetch_coaches',
    'fetch_schedule',
    'get_school',
    'get_roster',
    'get_coaches',
    'get_schedule',
    'list_schools',
    'find_school',
]
