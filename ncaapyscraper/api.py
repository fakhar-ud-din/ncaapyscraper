import asyncio

from concurrent.futures import ThreadPoolExecutor

from ncaapyscraper.client import Fetcher
from ncaapyscraper.output import school_result
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


def flatten(result, key):
    "One flat list across sports, handy for pandas"
    rows = []
    for sport in result['sports']:
        for record in sport.get(key) or []:
            rows.append({'school': result['school'], 'sport': sport['sport'], 'season': sport['season'], **record})

    return rows


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


def list_schools(conference=None, division=None):
    "Supported schools, filter by conference (sec, big10, 'Big Sky') or division (1, 2, 3, fbs, fcs)"
    fields = ['key', 'name', 'conference', 'division', 'subdivision', 'state', 'site', 'platform']
    return [{field: SCHOOLS[key][field] for field in fields} for key in pick_schools(conference, division)]
