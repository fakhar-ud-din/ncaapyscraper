import asyncio
import json
import logging
import re

from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlencode, urlparse
from zoneinfo import ZoneInfo

from ncaapyscraper.constants import *
from ncaapyscraper.utils import clean, clean_value, snake_case, sport_key, split_arg, to_number


logger = logging.getLogger('ncaapyscraper')


def ncaa_sport(sport):
    "mens-basketball"
    "Men's Basketball"
    "basketball-men"
    key = sport_key(sport)
    key = NCAA_SPORT_ALIASES.get(key, key)

    for name, config in NCAA_SPORTS.items():
        if key in (name, config['slug']):
            return {'key': name, **config}

    raise ValueError(f'Unknown sport "{sport}", ncaa.com has {", ".join(NCAA_SPORTS)}')


def ncaa_division(sport, division=None):
    "1, d1, fbs"
    division = str(division or sport['divisions'][0]).lower()
    division = division.isdigit() and f'd{division}' or division

    if division not in sport['divisions']:
        raise ValueError(f'{sport["key"]} on ncaa.com has divisions {", ".join(sport["divisions"])}')

    return division


def division_id(sport, division):
    if sport.get('national') and division == 'd1':
        return 0

    return NCAA_DIVISIONS[division]


def ncaa_season(day):
    "Seasons go by the year they start in, a May softball game is in the season that began the August before"
    return day.year if day.month >= 8 else day.year - 1


def to_date(value=None):
    "2026-11-07, today in US Eastern time when left out"
    if not value:
        return datetime.now(ZoneInfo(DEFAULT_TIMEZONE)).date()

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    return date.fromisoformat(str(value)[:10])


class NcaaParser:
    "Flat rows from ncaa.com's GraphQL responses and its rankings, standings and stats pages"

    def page_settings(self, page):
        "The JSON every ncaa.com page keeps its config in, query hashes and current week included"
        raw = page.css('script[data-drupal-selector="drupal-settings-json"]::text').get()
        return raw and json.loads(raw) or {}

    def parse_contests(self, contests, sport, division, variables):
        for contest in contests:
            teams = contest.get('teams') or []
            has_time = contest.get('hasStartTime') and contest.get('startTimeEpoch')

            row = {
                'game_id': str(contest.get('contestId')),
                'sport': sport['key'],
                'division': division,
                'season': variables['seasonYear'],
                'week': variables.get('week'),
                'date': contest.get('startDate') and datetime.strptime(contest['startDate'], '%m/%d/%Y').strftime('%Y-%m-%d'),
                'time': has_time and datetime.strptime(contest['startTime'], '%H:%M').strftime('%I:%M %p').lstrip('0') or None,
                'datetime_utc': has_time and datetime.fromtimestamp(contest['startTimeEpoch'], timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ') or None,
                'status': GAME_STATES.get(contest.get('gameState')) or clean(contest.get('statusCodeDisplay')),
                'period': clean(contest.get('currentPeriod')) or None,
                'clock': clean(contest.get('contestClock')) or None,
                'round': clean(contest.get('roundDescription')) or None,
                'is_championship': bool(contest.get('isChampionship')),
                'url': f"{NCAA_COM}{contest.get('url')}",
            }

            for side, is_home in [('home', True), ('away', False)]:
                team = next((team for team in teams if bool(team.get('isHome')) == is_home), {})
                row[f'{side}_team'] = clean(team.get('nameShort'))
                row[f'{side}_seoname'] = team.get('seoname')
                row[f'{side}_conference'] = team.get('conferenceSeo')
                row[f'{side}_score'] = team.get('score')
                row[f'{side}_rank'] = team.get('teamRank')
                row[f'{side}_seed'] = team.get('seed')
                row[f'{side}_winner'] = team.get('isWinner')

            yield row

    def parse_boxscore(self, boxscore, sport):
        teams = {str(team.get('teamId')): team for team in boxscore.get('teams') or []}

        for team_box in boxscore.get('teamBoxscore') or []:
            team = teams.get(str(team_box.get('teamId'))) or {}
            players = {}

            # Football lists a player once per category (passing, rushing...), one row per player is easier to use
            for stats in team_box.get('playerStats') or []:
                first_name, last_name = clean(stats.get('firstName')), clean(stats.get('lastName'))
                shirt_no = clean(stats.get('number')) or None
                key = (first_name, last_name, shirt_no)

                if key not in players:
                    players[key] = {
                        'game_id': str(boxscore.get('contestId')),
                        'sport': sport['key'],
                        'team': clean(team.get('nameShort')),
                        'team_id': str(team_box.get('teamId')),
                        'is_home': bool(team.get('isHome')),
                        'name': clean(f'{first_name or ""} {last_name or ""}'),
                        'first_name': first_name or None,
                        'last_name': last_name or None,
                        'shirt_no': shirt_no,
                        'position': clean(stats.get('position')) or None,
                    }

                players[key].update(self.stat_fields(stats))

            yield from players.values()

    def stat_fields(self, stats, prefix=''):
        "rushingYards -> rushing_yards, batterStats.hits -> batter_hits"
        fields = {}
        for key, value in stats.items():
            if key in BOXSCORE_PLAYER_KEYS:
                continue

            name = f'{prefix}{snake_case(key)}'
            if isinstance(value, dict):
                fields.update(self.stat_fields(value, f"{re.sub(r'_stats$', '', name)}_"))
            elif not isinstance(value, list):
                fields[name] = to_number(value)

        return fields

    def table_rows(self, table):
        "Rank, School, Rush Yds -> rank, school, rush_yds"
        headings = [snake_case(" ".join(th.css('::text').getall())) for th in table.css('thead th')]
        headings = [STAT_HEADINGS.get(heading, heading) for heading in headings]

        for row in table.css('tbody tr'):
            cells = [clean_value(" ".join(td.css('::text').getall())) for td in row.css('td')]
            yield {heading: to_number(cell) for heading, cell in zip(headings, cells) if heading}

    def parse_rankings(self, page):
        poll = clean(page.css('#edit-rankings-menu option[selected]::text').get() or page.css('title::text').get())
        updated = clean(page.css('.rankings-last-updated::text').get()) or None

        for table in page.css('table')[:1]:
            for row in self.table_rows(table):
                # Georgia (53), first place votes in brackets
                match = re.match(r'^(.*?)\s*\((\d+)\)$', str(row.get('school') or ''))
                if match:
                    row['school'], row['first_place_votes'] = match.group(1), int(match.group(2))

                yield {'poll': poll, 'updated': updated, **row}

    def parse_standings(self, page):
        for conference in page.css('.standings-conference'):
            for table in conference.xpath('following-sibling::*[1]').css('table')[:1]:
                columns = self.standings_columns(table)

                for row in table.css('tbody tr'):
                    cells = [clean_value(" ".join(td.css('::text').getall())) for td in row.css('td')]
                    yield {'conference': clean(conference.css('::text').get()), **{column: to_number(cell) for column, cell in zip(columns, cells)}}

    def standings_columns(self, table):
        "School | Conference W L | Overall W L PF PA -> school, conference_w ... overall_pa"
        groups = [snake_case(" ".join(th.css('::text').getall())) for th in table.css('.standings-table-header th')][1:]
        sub_headings = [snake_case(" ".join(th.css('::text').getall())) for th in table.css('.standings-table-subheader th')][1:]

        # colspan isn't reliable, every group starts again with W, so a repeat means the next group began
        columns, group, seen = ['school'], 0, set()
        for sub_heading in sub_headings:
            if sub_heading in seen and group < len(groups) - 1:
                group, seen = group + 1, set()

            seen.add(sub_heading)
            columns.append(f'{groups[group]}_{sub_heading}' if groups else sub_heading)

        return columns

    def parse_stat_list(self, page):
        for stat_type in ['individual', 'team']:
            for option in page.css(f'#select-container-{stat_type} option'):
                value = option.attrib.get('value')
                if value:
                    yield {'id': value.rstrip('/').split('/')[-1], 'name': clean(option.css('::text').get()), 'type': stat_type}

    def parse_stats(self, page):
        stat = clean(page.css('.stats-header__lower__title::text').get())

        for table in page.css('.block-stats__stats-table')[:1]:
            for row in self.table_rows(table):
                yield {'stat': stat, **row}

    def stats_pages(self, page):
        "Leaders come 50 a page, /p2, /p3..."
        path = urlparse(page.url).path.rstrip('/')
        return max([int(number) for number in re.findall(rf'{re.escape(path)}/p(\d+)', page.text)], default=1)


class NcaaClient:
    "Scoreboards, box scores, rankings, standings and stat leaders from ncaa.com"

    # Shared, once a client picks up new hashes every client uses them
    queries = dict(NCAA_QUERIES)

    def __init__(self, fetcher):
        self.fetcher = fetcher
        self.parser = NcaaParser()

    def sport_url(self, page_type, sport, division=None):
        "https://www.ncaa.com/standings/basketball-men/d1"
        sport = ncaa_sport(sport)
        division = ncaa_division(sport, division)
        return sport, division, f"{NCAA_COM}/{page_type}/{sport['slug']}/{division}"

    async def settings(self, url):
        return self.parser.page_settings(await self.fetcher.get_or_fail(url))

    async def query(self, name, variables, page_url):
        "One GraphQL query, page_url is the ncaa.com page that makes it, for when its hash is out of date"
        for attempt in range(2):
            # The server only finds the hash in compact json, a space after a colon is a 500
            url = NCAA_GRAPHQL + '?' + urlencode({
                'meta': name,
                'extensions': json.dumps({'persistedQuery': {'version': 1, 'sha256Hash': self.queries.get(name)}}, separators=(',', ':')),
                'variables': json.dumps(variables, separators=(',', ':')),
            })
            data = (await self.fetcher.get_or_fail(url)).json()
            errors = [error.get('message') for error in data.get('errors') or []]

            if 'PersistedQueryNotFound' in errors and not attempt:
                await self.refresh_queries(page_url)
                continue

            if errors:
                raise ValueError(f'ncaa.com {name} failed: {"; ".join(map(str, errors))}')

            return data.get('data') or {}

    async def refresh_queries(self, page_url):
        "ncaa.com deployed new queries, its own pages list the new hashes"
        settings = await self.settings(page_url)
        self.queries.update((settings.get('scoreboardWidget') or {}).get('shas') or {})
        self.queries.update((settings.get('gamecenter') or {}).get('gqlShas') or {})

    async def current_week(self, page_url):
        scoreboard = (await self.settings(page_url)).get('scoreboard') or {}
        week = str((scoreboard.get('currentDate') or {}).get('week') or 1)

        # P is the postseason, ncaa.com files bowl games under week 16
        return scoreboard.get('seasonYear'), week.isdigit() and int(week) or 16

    async def scoreboard(self, sport, day=None, division=None, week=None, season=None):
        "Every game on a day, football goes by week instead"
        sport, division, page_url = self.sport_url('scoreboard', sport, division)
        variables = {'sportCode': sport['code'], 'division': division_id(sport, division)}

        if sport['key'] == 'football':
            if week is None:
                page_season, week = await self.current_week(page_url)
                season = season or page_season

            variables.update(seasonYear=int(season or ncaa_season(to_date())), contestDate=None, week=int(week))
        else:
            day = to_date(day)
            variables.update(seasonYear=int(season or ncaa_season(day)), contestDate=day.strftime('%m/%d/%Y'), week=None)

        data = await self.query('GetContests_web', variables, page_url)
        return list(self.parser.parse_contests(data.get('contests') or [], sport, division, variables))

    async def boxscore(self, game_id, sport=None):
        "Player stats for one game, one row per player"
        game_url = f'{NCAA_COM}/game/{game_id}'

        if not sport:
            # The game page knows the sport, and has fresh query hashes while we're there
            gamecenter = (await self.settings(game_url)).get('gamecenter') or {}
            self.queries.update(gamecenter.get('gqlShas') or {})
            sport = gamecenter.get('sportGender')

        sport = ncaa_sport(sport)
        if not sport['boxscore']:
            raise ValueError(f"ncaa.com has no box scores for {sport['key']}")

        name = f"NCAA_GetGamecenterBoxscore{sport['boxscore']}ById_web"
        data = await self.query(name, {'contestId': str(game_id), 'staticTestEnv': None}, game_url)
        return list(self.parser.parse_boxscore(data.get('boxscore') or {}, sport))

    async def rankings(self, sport, division=None, poll=None):
        "poll is the last part of the ncaa.com url, e.g. associated-press. Without it, the default poll"
        sport, division, url = self.sport_url('rankings', sport, division)
        page = await self.fetcher.get_or_fail(poll and f'{url}/{poll}' or url)
        return list(self.parser.parse_rankings(page))

    async def standings(self, sport, division=None):
        sport, division, url = self.sport_url('standings', sport, division)
        rows = list(self.parser.parse_standings(await self.fetcher.get_or_fail(url)))

        # The page is there for every sport, but only football and basketball have tables on it
        if not rows:
            raise ValueError(f"ncaa.com has no standings for {sport['key']} {division}")

        return rows

    async def stat_list(self, sport, division=None):
        "Every stat ncaa.com ranks for a sport, individual and team"
        sport, division, url = self.sport_url('stats', sport, division)
        return list(self.parser.parse_stat_list(await self.fetcher.get_or_fail(url)))

    async def stats(self, sport, stat, division=None, team=False):
        "National leaders for one stat, stat is its name (Rushing Yards) or id (469)"
        stat_type = team and 'team' or 'individual'
        stat_id = str(stat)

        if not stat_id.isdigit():
            stats = [row for row in await self.stat_list(sport, division) if row['type'] == stat_type]
            found = [row for row in stats if row['name'].lower() == stat_id.lower()]
            if not found:
                raise ValueError(f'Unknown {stat_type} stat "{stat}", ncaa.com has {", ".join(row["name"] for row in stats)}')

            stat_id = found[0]['id']

        sport, division, url = self.sport_url('stats', sport, division)
        url = f'{url}/current/{stat_type}/{stat_id}'

        first = await self.fetcher.get_or_fail(url)
        pages = [first] + list(await asyncio.gather(*[
            self.fetcher.get_or_fail(f'{url}/p{number}') for number in range(2, self.parser.stats_pages(first) + 1)
        ]))

        rows = [row for page in pages for row in self.parser.parse_stats(page)]

        # Ties show a dash instead of a rank, even across pages, they share the rank above
        for previous, row in zip(rows, rows[1:]):
            row['rank'] = row.get('rank') or previous.get('rank')

        return rows

    async def games(self, since, until, sports=None, boxscores=False):
        "Every game between two dates in every division, plus box scores of the finished ones"
        sports = [ncaa_sport(sport) for sport in split_arg(sports) or NCAA_SPORTS]
        days = [since + timedelta(days=offset) for offset in range((until - since).days + 1)]

        tasks = []
        for sport in sports:
            for division in sport['divisions']:
                if sport['key'] == 'football':
                    tasks.append(self.football_games(division, since, until))
                else:
                    tasks += [self.scoreboard(sport['key'], day, division) for day in days]

        # A game between divisions shows up on both scoreboards
        games = {game['game_id']: game for result in await self.gather(tasks) for game in result}
        games = list(games.values())

        players = []
        if boxscores:
            finished = [game for game in games if game['status'] == 'final' and NCAA_SPORTS[game['sport']]['boxscore']]
            results = await self.gather([self.boxscore(game['game_id'], game['sport']) for game in finished])
            players = [player for result in results for player in result]

        return games, players

    async def football_games(self, division, since, until):
        "Football only goes by week, so every week so far, kept to the dates asked for"
        _, _, page_url = self.sport_url('scoreboard', 'football', division)
        season, current = await self.current_week(page_url)

        weeks = await self.gather([self.scoreboard('football', division=division, week=week, season=season) for week in range(1, current + 1)])
        return [game for week in weeks for game in week if game['date'] and since.isoformat() <= game['date'] <= until.isoformat()]

    async def gather(self, tasks):
        "One failed day or game shouldn't stop the rest"
        results = []
        for result in await asyncio.gather(*tasks, return_exceptions=True):
            if isinstance(result, Exception):
                logger.warning(repr(result))
            else:
                results.append(result)

        return results
