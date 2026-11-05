from w3lib.url import add_or_replace_parameters as aorp

from ncaapyscraper.constants import *
from ncaapyscraper.items import PlayerItem, TeamScheduleItem
from ncaapyscraper.platforms.base import BaseParser, BaseCrawler
from ncaapyscraper.utils import (
    clean,
    clean_bio,
    sports_gender,
    slugify,
    format_height,
    format_weight,
    format_score,
    to_local,
    utc_text,
)


class WmtParser(BaseParser):
    def parse_players(self, response, data):
        meta = response.meta

        for roster_player in data.get('data') or []:
            player = roster_player.get('player') or {}
            item = self.base_item(PlayerItem(), meta)

            item["season"] = self.roster_season(roster_player) or meta.get('season')
            item["first_name"] = clean(player.get('first_name'))
            item["last_name"] = clean(player.get('last_name'))
            item["name"] = clean(player.get('full_name'))
            item["shirt_no"] = clean(roster_player.get('jersey_number_label') or roster_player.get('jersey_number'))
            item["position"] = self.player_position(roster_player)
            item["height"] = format_height(
                roster_player.get('height_feet') or player.get('height_feet'),
                roster_player.get('height_inches') or player.get('height_inches'),
            )
            item["weight"] = format_weight(roster_player.get('weight') or player.get('weight'))
            item["player_class"] = clean((roster_player.get('class_level') or {}).get('name'))
            item["hometown"] = clean(player.get('hometown'))
            item["highschool"] = clean(player.get('high_school'))
            item["previous_school"] = clean(player.get('previous_school'))
            item["major"] = clean(player.get('major'))
            item["bio"] = clean_bio(roster_player.get('short_biography') or player.get('short_master_biography'))
            item["image_url"] = (roster_player.get('photo') or {}).get('url') or ''
            item["profile_url"] = self.BASE_URL.format(f"/sports/{meta['slug']}/roster/player/{player.get('slug')}")
            item["gender"] = self.player_gender(player.get('gender'), meta)
            item["is_athlete"], item["is_coach"] = 1, 0

            yield item

    def parse_coaches(self, response, data):
        meta = response.meta

        for staff in data.get('data') or []:
            member = staff.get('staff_member') or {}
            item = self.base_item(PlayerItem(), meta)

            item["season"] = self.roster_season(staff) or meta.get('season')
            item["first_name"] = clean(member.get('first_name'))
            item["last_name"] = clean(member.get('last_name'))
            item["name"] = clean(member.get('full_name') or f'{item["first_name"] or ""} {item["last_name"] or ""}')
            item["title"] = clean(staff.get('position'))
            item["image_url"] = (staff.get('photo') or {}).get('url') or ''
            item["profile_url"] = self.staff_website_url(meta, staff, member)
            item["is_athlete"], item["is_coach"] = 0, 1

            yield item

    def parse_schedule(self, response, data):
        meta = response.meta

        for event in data.get('data') or []:
            item = self.base_item(TeamScheduleItem(), meta)
            start = to_local(event.get('datetime'), meta.get('timezone'))

            item["date"] = start and start.strftime('%Y-%m-%d') or ''
            item["time"] = self.schedule_time(event, start)
            item["datetime_utc"] = utc_text(event.get('datetime'))
            item["opponent"] = clean(event.get('opponent_name') or (event.get('opponent') or {}).get('name'))
            item["home_away"] = clean(event.get('venue_type'))
            item["location"] = clean(event.get('location'))
            item["venue"] = clean(event.get('venue'))
            item["is_conference"] = int(bool(event.get('is_conference')))
            item["result"], item["score"] = self.schedule_result(event.get('schedule_event_result') or {})
            item["image_url"] = (event.get('opponent_logo') or {}).get('url') or ''

            yield item

    def schedule_time(self, event, start):
        if event.get('is_all_day'):
            return 'All Day'

        if event.get('tba'):
            return clean(event.get('tba_text')) or 'TBA'

        return start and start.strftime('%I:%M %p').lstrip('0') or ''

    def schedule_result(self, result):
        outcome = RESULT_MAP.get(result.get('result') or '', '')
        winning = format_score(result.get('winning_score'))
        losing = format_score(result.get('losing_score'))

        if not outcome or not winning or not losing:
            return outcome, ''

        if outcome == 'L':
            return outcome, f'{losing}-{winning}'

        return outcome, f'{winning}-{losing}'

    def roster_season(self, record):
        return clean(((record.get('roster') or {}).get('season') or {}).get('name'))

    def player_position(self, roster_player):
        position = roster_player.get('player_position') or {}
        return clean(position.get('abbreviation') or position.get('name')) or ''

    def staff_website_url(self, meta, staff, member):
        season = slugify(self.roster_season(staff) or '')
        return self.BASE_URL.format(f"/sports/{meta['slug']}/roster/season/{season}/staff/{member.get('slug')}")


class WmtCrawler(BaseCrawler):
    parser_class = WmtParser
    start_path = '/website-api/website-config'

    per_page = 100
    player_includes = 'player,classLevel,playerPosition,photo,roster.season'
    staff_includes = 'staffMember,photo,roster.season'
    schedule_includes = 'opponent,opponentLogo,scheduleEventResult'

    def api_url(self, path, **params):
        return aorp(self.BASE_URL.format(f'/website-api{path}'), {key: str(value) for key, value in params.items()})

    async def crawl(self):
        config = self.load_json(await self.get(self.BASE_URL.format(self.start_path), api=True)) or {}
        settings = (config.get('data') or config).get('settings') or {}
        timezone = settings.get('website_timezone') or DEFAULT_TIMEZONE

        page = await self.start(self.api_url('/sports', per_page=100), api=True)

        tasks = []
        for sport in (self.load_json(page) or {}).get('data') or []:
            if not sport.get('default_roster_id') and not sport.get('schedule_id'):
                continue

            meta = {
                "sports_name": clean(sport['name']),
                "slug": sport['slug'],
                "gender": GENDER_MAP.get((sport.get('gender') or '').lower()) or sports_gender(sport['name']),
                "timezone": timezone,
            }

            if not self.wants_sport(meta['sports_name'], meta['slug'], meta['gender']):
                continue

            if sport.get('default_roster_id') and self.wants('players', 'coaches'):
                tasks.append(self.crawl_roster(sport['default_roster_id'], meta))

            # Some sports have rosters but no default one set, take the newest
            elif self.wants('players', 'coaches'):
                tasks.append(self.crawl_latest_roster(sport['id'], meta))

            if sport.get('schedule_id') and self.wants('schedules'):
                tasks.append(self.crawl_schedule(sport['schedule_id'], meta))

        await self.gather(*tasks)

    async def crawl_latest_roster(self, sport_id, meta):
        page = await self.get(self.api_url('/rosters', sort='-id', per_page=1, **{'filter[sport_id]': sport_id}), meta, api=True)
        rosters = (self.load_json(page) or {}).get('data') or []
        if rosters:
            await self.crawl_roster(rosters[0]['id'], meta)

    async def crawl_roster(self, roster_id, meta):
        roster = {'filter[roster_id]': roster_id, 'per_page': self.per_page}

        tasks = []
        if self.wants('players'):
            tasks.append(self.crawl_pages(self.api_url('/player-rosters', include=self.player_includes, **roster), meta, self.parser.parse_players))

        if self.wants('coaches'):
            tasks.append(self.crawl_pages(self.api_url('/roster-staff-members', include=self.staff_includes, **roster), meta, self.parser.parse_coaches))

        await self.gather(*tasks)

    async def crawl_schedule(self, schedule_id, meta):
        page = await self.get(self.api_url(f'/schedules/{schedule_id}', include='season'), meta, api=True)
        schedule = (self.load_json(page) or {}).get('data') or {}
        if not schedule.get('id'):
            return

        meta = {**meta, 'season': clean((schedule.get('season') or {}).get('name'))}
        events = {'filter[schedule_id]': schedule['id'], 'per_page': self.per_page, 'sort': 'datetime'}

        await self.crawl_pages(self.api_url('/schedule-events', include=self.schedule_includes, **events), meta, self.parser.parse_schedule)

    async def crawl_pages(self, url, meta, parse):
        while url:
            page = await self.get(url, meta, api=True)
            if not page:
                return

            data = self.load_json(page) or {}
            self.keep(parse(page, data))
            url = self.next_page(page, data)

    def next_page(self, page, data):
        info = data.get('meta') or {}
        current_page = info.get('current_page') or 1

        if current_page < (info.get('last_page') or 1):
            return aorp(page.url, {'page': str(current_page + 1)})

        return None
