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
    format_time,
    utc_text,
)


class SidearmParser(BaseParser):
    def parse_players(self, response, roster):
        meta = {**response.meta, 'season': (roster.get('season') or {}).get('title')}

        for player in roster.get('players') or []:
            item = self.base_item(PlayerItem(), meta)

            item["first_name"] = clean(player.get('firstName'))
            item["last_name"] = clean(player.get('lastName'))
            item["name"] = clean(f'{item["first_name"] or ""} {item["last_name"] or ""}')
            item["shirt_no"] = clean(player.get('jerseyNumber'))
            item["position"] = clean(player.get('positionShort') or player.get('positionLong'))
            item["height"] = format_height(player.get('heightFeet'), player.get('heightInches'))
            item["weight"] = format_weight(player.get('weight'))
            item["player_class"] = clean(player.get('academicYearLong') or player.get('academicYearShort'))
            item["hometown"] = clean(player.get('hometown'))
            item["highschool"] = clean(player.get('highSchool'))
            item["previous_school"] = clean(player.get('previousSchool'))
            item["major"] = clean(player.get('major'))
            item["bio"] = clean_bio(player.get('bio'))
            item["image_url"] = self.player_image_url(player)
            item["profile_url"] = self.player_website_url(meta, player)
            item["gender"] = self.player_gender(player.get('gender'), meta)
            item["is_athlete"], item["is_coach"] = 1, 0

            yield item

    def parse_coaches(self, response, roster):
        meta = {**response.meta, 'season': (roster.get('season') or {}).get('title')}

        coaches = [('coaches', coach) for coach in roster.get('coaches') or []]
        coaches += [('staff', staff) for staff in roster.get('support') or []]

        for coach_or_staff, coach in coaches:
            item = self.base_item(PlayerItem(), meta)

            item["first_name"] = clean(coach.get('firstName'))
            item["last_name"] = clean(coach.get('lastName'))
            item["name"] = clean(f'{item["first_name"] or ""} {item["last_name"] or ""}')
            item["title"] = clean(coach.get('title'))
            item["bio"] = clean_bio(coach.get('bio'))
            item["image_url"] = self.player_image_url(coach)
            item["profile_url"] = self.staff_website_url(meta, coach, coach_or_staff)
            item["is_athlete"], item["is_coach"] = 0, 1

            yield item

    def parse_schedule(self, response, schedule):
        meta = {**response.meta, 'season': (schedule.get('season') or {}).get('title')}

        for game in schedule.get('games') or []:
            item = self.base_item(TeamScheduleItem(), meta)
            opponent = game.get('opponent') or {}

            item["date"] = (game.get('date') or '')[:10]
            item["time"] = format_time(game.get('time'))
            item["datetime_utc"] = utc_text(game.get('dateUtc'))
            item["opponent"] = clean(opponent.get('title') or game.get('eventName'))
            item["home_away"] = VENUE_MAP.get(game.get('locationIndicator'), '')
            item["location"] = clean(game.get('location'))
            item["venue"] = clean((game.get('facility') or {}).get('title'))
            item["is_conference"] = int(bool(game.get('conference')))
            item["result"], item["score"] = self.schedule_result(game.get('result') or {})
            item["tournament"] = self.schedule_tournament(game)
            item["tv"] = clean((game.get('media') or {}).get('tv'))
            item["image_url"] = self.absolute_url((opponent.get('image') or {}).get('fullpath'))

            yield item

    def schedule_result(self, result):
        team_score = clean(result.get('teamScore'))
        opponent_score = clean(result.get('opponentScore'))
        score = team_score and opponent_score and f'{team_score}-{opponent_score}' or ''

        return RESULT_MAP.get(result.get('status'), ''), score

    def schedule_tournament(self, game):
        tournament = game.get('tournament')
        if isinstance(tournament, dict):
            return clean(tournament.get('title'))

        return clean(tournament) or ''

    def player_image_url(self, player):
        image = player.get('image') or {}
        return image.get('absoluteUrl') or self.absolute_url(image.get('url'))

    def player_website_url(self, meta, player):
        name = slugify(f'{player.get("firstName")}-{player.get("lastName")}')
        return self.BASE_URL.format(f"/sports/{meta['slug']}/roster/{name}/{player.get('rosterPlayerId')}")

    def staff_website_url(self, meta, profile, coach_or_staff):
        name = slugify(f'{profile.get("firstName")}-{profile.get("lastName")}')
        return self.BASE_URL.format(f"/sports/{meta['slug']}/roster/{coach_or_staff}/{name}/{profile.get('id')}")


class SidearmCrawler(BaseCrawler):
    parser_class = SidearmParser
    start_path = '/api/v2/Sports'

    async def crawl(self):
        page = await self.start(self.BASE_URL.format(self.start_path), api=True)

        tasks = []
        for sport in self.load_json(page) or []:
            if not sport.get('rosterId') and not sport.get('scheduleId'):
                continue

            meta = {
                "sports_name": clean(sport['title']),
                "slug": sport['globalSportNameSlug'],
                "gender": GENDER_MAP.get((sport.get('globalSportGender') or '').lower()) or sports_gender(sport['title']),
            }

            if not self.wants_sport(meta['sports_name'], meta['slug'], meta['gender']):
                continue

            if sport.get('rosterId') and self.wants('players', 'coaches'):
                tasks.append(self.crawl_roster(self.BASE_URL.format(f"/api/v2/Rosters/{sport['rosterId']}"), meta))

            if sport.get('scheduleId') and self.wants('schedules'):
                tasks.append(self.crawl_schedule(self.BASE_URL.format(f"/api/v2/Schedule/{sport['scheduleId']}"), meta))

        await self.gather(*tasks)

    async def crawl_roster(self, url, meta):
        page = await self.get(url, meta, api=True)
        roster = self.load_json(page)
        if not roster:
            return

        self.keep(self.parser.parse_players(page, roster))

        if not self.wants('coaches'):
            return

        if roster.get('coaches') or roster.get('support'):
            self.keep(self.parser.parse_coaches(page, roster))
            return

        # Some sites only send coaches back with includeCoaches on the bySport endpoint
        season = (roster.get('season') or {}).get('title')
        if season:
            url = self.BASE_URL.format(f"/api/v2/Rosters/bySport/{meta['slug']}?season={season}&includeCoaches=true")
            page = await self.get(url, self.sport_meta(page), api=True)
            roster = self.load_json(page)
            if roster:
                self.keep(self.parser.parse_coaches(page, roster))

    async def crawl_schedule(self, url, meta):
        page = await self.get(url, meta, api=True)
        schedule = self.load_json(page)
        if schedule:
            self.keep(self.parser.parse_schedule(page, schedule))
