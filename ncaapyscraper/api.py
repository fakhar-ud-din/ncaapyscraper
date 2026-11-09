import asyncio

from concurrent.futures import ThreadPoolExecutor

from ncaapyscraper.client import Fetcher
from ncaapyscraper.ncaa import NcaaClient
from ncaapyscraper.output import flatten, school_result
from ncaapyscraper.platforms import PLATFORMS
from ncaapyscraper.schools import SCHOOLS, find_school, pick_schools


async def fetch_school(school, sports=None, data=None, gender=None, bios=True, fetcher=None):
    "Everything for one school, the same dict the cli saves as json"
    found = find_school(school)
    if not found:
        raise ValueError(f'Unknown school "{school}", see ncaapyscraper.list_schools()')

    own_fetcher = fetcher is None
    fetcher = fetcher or Fetcher()

    try:
        crawler = PLATFORMS[found['platform']](found, fetcher, sports=sports, data=data, gender=gender)
        await crawler.crawl()
        return school_result(found, crawler.items, crawler.data, bios)
    finally:
        if own_fetcher:
            await fetcher.close()


async def fetch_schools(schools, parallel=4, **kwargs):
    "Yields (school, result) as each one finishes, result is the exception if it failed"
    async with Fetcher() as fetcher:
        semaphore = asyncio.Semaphore(max(parallel, 1))

        async def one(school):
            async with semaphore:
                try:
                    return school, await fetch_school(school, fetcher=fetcher, **kwargs)
                except Exception as error:
                    return school, error

        for task in asyncio.as_completed([one(school) for school in schools]):
            yield await task


async def fetch_roster(school, sport=None, gender=None, bios=True):
    result = await fetch_school(school, sports=sport, data=['players'], gender=gender, bios=bios)
    return flatten(result, 'players')


async def fetch_coaches(school, sport=None, gender=None, bios=True):
    result = await fetch_school(school, sports=sport, data=['coaches'], gender=gender, bios=bios)
    return flatten(result, 'coaches')


async def fetch_schedule(school, sport=None, gender=None):
    result = await fetch_school(school, sports=sport, data=['schedules'], gender=gender)
    return flatten(result, 'schedule')


async def with_ncaa(call):
    "Runs call(client) on an ncaa.com client with a fetcher of its own"
    async with Fetcher() as fetcher:
        return await call(NcaaClient(fetcher))


async def fetch_scoreboard(sport, date=None, division=None, week=None, season=None):
    return await with_ncaa(lambda ncaa: ncaa.scoreboard(sport, date, division, week, season))


async def fetch_boxscore(game_id, sport=None):
    return await with_ncaa(lambda ncaa: ncaa.boxscore(game_id, sport))


async def fetch_rankings(sport, division=None, poll=None):
    return await with_ncaa(lambda ncaa: ncaa.rankings(sport, division, poll))


async def fetch_standings(sport, division=None):
    return await with_ncaa(lambda ncaa: ncaa.standings(sport, division))


async def fetch_stat_list(sport, division=None):
    return await with_ncaa(lambda ncaa: ncaa.stat_list(sport, division))


async def fetch_stats(sport, stat, division=None, team=False):
    return await with_ncaa(lambda ncaa: ncaa.stats(sport, stat, division, team))


async def fetch_games(since, until, sports=None, boxscores=False):
    "(games, box score rows) for every game between two dates, what the weekly season files are built from"
    return await with_ncaa(lambda ncaa: ncaa.games(since, until, sports, boxscores))


def run_sync(coroutine):
    "asyncio.run, but also works in Jupyter where a loop is already running"
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coroutine)

    with ThreadPoolExecutor(1) as pool:
        return pool.submit(asyncio.run, coroutine).result()


def get_school(school, sports=None, data=None, gender=None, bios=True):
    return run_sync(fetch_school(school, sports=sports, data=data, gender=gender, bios=bios))


def get_roster(school, sport=None, gender=None, bios=True):
    return run_sync(fetch_roster(school, sport=sport, gender=gender, bios=bios))


def get_coaches(school, sport=None, gender=None, bios=True):
    return run_sync(fetch_coaches(school, sport=sport, gender=gender, bios=bios))


def get_schedule(school, sport=None, gender=None):
    return run_sync(fetch_schedule(school, sport=sport, gender=gender))


def get_scoreboard(sport, date=None, division=None, week=None, season=None):
    "Every game on a day (default today), football goes by week (default the current one)"
    return run_sync(fetch_scoreboard(sport, date, division, week, season))


def get_boxscore(game_id, sport=None):
    "Player stats for one game, game_id is the number in an ncaa.com game url"
    return run_sync(fetch_boxscore(game_id, sport))


def get_rankings(sport, division=None, poll=None):
    "poll is the end of the ncaa.com rankings url, e.g. associated-press. Default is ncaa.com's default poll"
    return run_sync(fetch_rankings(sport, division, poll))


def get_standings(sport, division=None):
    return run_sync(fetch_standings(sport, division))


def get_stat_list(sport, division=None):
    "Every stat ncaa.com has national leaders for, individual and team"
    return run_sync(fetch_stat_list(sport, division))


def get_stats(sport, stat, division=None, team=False):
    "National leaders for one stat, by name (Rushing Yards) or id (469)"
    return run_sync(fetch_stats(sport, stat, division, team))


def list_schools(conference=None, division=None):
    "Supported schools, filter by conference (sec, big10, 'Big Sky') or division (1, 2, 3, fbs, fcs)"
    fields = ['key', 'name', 'conference', 'division', 'subdivision', 'state', 'site', 'platform']
    return [{field: SCHOOLS[key][field] for field in fields} for key in pick_schools(conference, division)]
