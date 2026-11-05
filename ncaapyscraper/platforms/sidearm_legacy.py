import json
import re

from urllib.parse import unquote

from ncaapyscraper.constants import *
from ncaapyscraper.items import PlayerItem, TeamScheduleItem
from ncaapyscraper.platforms.base import BaseParser, BaseCrawler
from ncaapyscraper.utils import (
    clean,
    clean_bio,
    sports_gender,
    slugify,
    normalize_height,
    format_height,
    format_weight,
    format_time,
    is_time,
    split_result,
    clean_opponent,
    parse_month_day,
    season_dates,
    season_year,
)
from ncaapyscraper.selectors import (
    sidearm_roster_css,
    sidearm_schedule_css,
    nextgen_schedule_css,
)


class SidearmLegacyParser(BaseParser):
    roster_css = sidearm_roster_css
    schedule_css = sidearm_schedule_css

    def parse_roster(self, response):
        css = self.roster_css
        meta = {**response.meta, 'season': self.page_season(response)}

        # Newer template renders the roster with Vue from a json object on the page
        roster = not response.css(css['player']) and self.embedded_json(response, r'roster:\s*(?=\{)', '#vue-rosters')
        if roster:
            yield from self.parse_roster_json(meta, roster)
            return

        # Nextgen person cards, the table view on the same page has everything
        if not response.css(css['player']):
            yield from self.parse_roster_tables(response, meta)
            return

        for player in response.css(css['player']):
            item = self.base_item(PlayerItem(), meta)

            item["name"] = self.css_text(player, css['name'])
            item["first_name"], item["last_name"] = self.player_first_last_names(item["name"])
            item["shirt_no"] = self.css_text(player, css['shirt_no'])
            item["position"] = self.css_text(player, css['position'])
            item["height"] = normalize_height(self.css_first(player, css['height']))
            item["weight"] = format_weight(self.css_first(player, css['weight']))
            item["player_class"] = self.css_last(player, css['player_class'])
            item["hometown"] = self.css_first(player, css['hometown'])
            item["highschool"] = self.css_first(player, css['highschool'])
            item["previous_school"] = self.css_first(player, css['previous_school'])
            item["major"] = self.css_first(player, css['major'])
            item["image_url"] = self.image_url(player.css(css['image_url']).get())
            item["profile_url"] = self.absolute_url(player.css(css['profile_url']).get())
            item["gender"] = self.player_gender(self.roster_section_gender(player), meta)
            item["is_athlete"], item["is_coach"] = 1, 0

            yield item

        seen = set()
        for coach in response.css(css['coach']):
            item = self.base_item(PlayerItem(), meta)

            item["name"] = self.css_text(coach, css['coach_name'])
            item["first_name"], item["last_name"] = self.player_first_last_names(item["name"])
            item["title"] = self.css_text(coach, css['coach_title'])
            item["image_url"] = self.image_url(coach.css(css['coach_image_url']).get())
            item["profile_url"] = self.absolute_url(coach.css(css['coach_profile_url']).get())
            item["is_athlete"], item["is_coach"] = 0, 1

            # Staff list shows up twice on some pages (screen and print)
            if not item["name"] or (item["name"], item["title"]) in seen:
                continue
            seen.add((item["name"], item["title"]))

            yield item

    def parse_schedule(self, response):
        css = self.schedule_css
        meta = {**response.meta, 'season': self.page_season(response)}

        games = response.css(css['card'])

        schedule = not games and self.embedded_json(response, r'"games":\s*(?=\[\{)', 'var schedule_id')
        if schedule:
            yield from self.parse_schedule_json(meta, schedule)
            return

        if not games and response.css(nextgen_schedule_css['card']):
            yield from self.parse_schedule_cards(response, meta)
            return

        events = self.schedule_events(response)

        if len(events) != len(games):
            month_days = [parse_month_day(self.css_text(game, css['date'])) for game in games]
            events = [(match_date, '') for match_date in season_dates(month_days, season_year(meta['season']))]

        for game, (match_date, event_time) in zip(games, events):
            item = self.base_item(TeamScheduleItem(), meta)
            match_time = next(iter(part for part in clean(game.css(css['date']).getall()) if is_time(part)), '')

            item["date"] = match_date
            item["time"] = format_time(match_time or event_time)
            item["opponent"] = clean_opponent(self.css_text(game, css['opponent']))
            item["home_away"] = self.schedule_home_away(game.attrib.get('class'))
            item["location"] = self.css_first(game, css['location'])
            item["venue"] = self.css_first(game, css['venue'])
            item["is_conference"] = int(bool(self.css_text(game, css['conference'])))
            item["result"], item["score"] = split_result(self.css_text(game, css['result']))
            item["tv"] = self.css_first(game, css['tv'])
            item["image_url"] = self.image_url(game.css(css['image_url']).get())

            yield item

    def parse_roster_json(self, meta, roster):
        meta = {**meta, 'season': (roster.get('season') or {}).get('title') or meta.get('season')}

        for player in roster.get('players') or []:
            item = self.base_item(PlayerItem(), meta)

            item["first_name"] = clean(player.get('first_name'))
            item["last_name"] = clean(player.get('last_name'))
            item["name"] = clean(f'{item["first_name"] or ""} {item["last_name"] or ""}')
            item["shirt_no"] = clean(player.get('jersey_number'))
            item["position"] = clean(player.get('position_short') or player.get('position_long'))
            item["height"] = format_height(player.get('height_feet'), player.get('height_inches'))
            item["weight"] = format_weight(player.get('weight'))
            item["player_class"] = clean(player.get('academic_year_long') or player.get('academic_year_short'))
            item["hometown"] = clean(player.get('hometown'))
            item["highschool"] = clean(player.get('highschool') or player.get('high_school'))
            item["previous_school"] = clean(player.get('previous_school'))
            item["major"] = clean(player.get('major'))
            item["bio"] = clean_bio(player.get('bio'))
            item["image_url"] = self.absolute_url((player.get('image') or {}).get('fullpath'))
            item["profile_url"] = self.profile_url(meta, 'roster', item["name"], player.get('rp_id'))
            item["gender"] = self.player_gender(player.get('gender'), meta)
            item["is_athlete"], item["is_coach"] = 1, 0

            yield item

        coaches = [('coaches', coach) for coach in roster.get('coaches') or []]
        coaches += [('staff', staff) for staff in roster.get('support') or []]

        for coach_or_staff, coach in coaches:
            item = self.base_item(PlayerItem(), meta)

            item["first_name"] = clean(coach.get('firstname') or coach.get('first_name'))
            item["last_name"] = clean(coach.get('lastname') or coach.get('last_name'))
            item["name"] = clean(f'{item["first_name"] or ""} {item["last_name"] or ""}')
            item["title"] = clean(coach.get('title'))
            item["image_url"] = self.absolute_url((coach.get('image') or {}).get('fullpath'))
            item["profile_url"] = self.profile_url(meta, f'roster/{coach_or_staff}', item["name"], coach.get('id'))
            item["is_athlete"], item["is_coach"] = 0, 1

            yield item

    def parse_schedule_json(self, meta, games):
        for game in games:
            item = self.base_item(TeamScheduleItem(), meta)
            opponent = game.get('opponent') or {}
            result = game.get('result') or {}

            team_score, opponent_score = clean(result.get('team_score')), clean(result.get('opponent_score'))

            item["date"] = (game.get('date') or '')[:10]
            item["time"] = format_time(game.get('time'))
            item["opponent"] = clean_opponent(opponent.get('title'))
            item["home_away"] = VENUE_MAP.get(game.get('location_indicator'), '')
            item["location"] = clean(game.get('location'))
            item["venue"] = clean((game.get('facility') or {}).get('title')) if isinstance(game.get('facility'), dict) else ''
            item["is_conference"] = int(bool(game.get('conference')))
            item["result"] = RESULT_MAP.get(clean(result.get('status')) or '', '')
            item["score"] = team_score and opponent_score and f'{team_score}-{opponent_score}' or ''
            item["tournament"] = clean((game.get('tournament') or {}).get('title')) if isinstance(game.get('tournament'), dict) else ''
            item["tv"] = clean((game.get('media') or {}).get('tv'))
            item["image_url"] = self.absolute_url((opponent.get('image') or {}).get('fullpath')) if isinstance(opponent.get('image'), dict) else ''

            yield item

    def parse_roster_tables(self, response, meta):
        for table in response.css('table'):
            rows = list(self.table_rows(table))
            if not rows or 'name' not in rows[0]:
                continue

            is_staff = 'title' in rows[0]
            for row in rows:
                item = self.base_item(PlayerItem(), meta)

                item["name"] = row.get('name') or ''
                item["first_name"], item["last_name"] = self.player_first_last_names(item["name"])
                item["image_url"] = self.image_url(row.get('image_url'))
                item["profile_url"] = self.absolute_url(row.get('profile_url'))

                if is_staff:
                    item["title"] = row.get('title')
                    item["is_athlete"], item["is_coach"] = 0, 1
                else:
                    item["shirt_no"] = row.get('shirt_no')
                    item["position"] = row.get('position')
                    item["height"] = normalize_height(row.get('height'))
                    item["weight"] = format_weight(row.get('weight'))
                    item["player_class"] = row.get('player_class')
                    item["hometown"] = self.player_hometown(row)
                    item["highschool"], item["previous_school"] = self.player_schools(row)
                    item["major"] = row.get('major')
                    item["is_athlete"], item["is_coach"] = 1, 0

                if item["name"]:
                    yield item

    def parse_schedule_cards(self, response, meta):
        css = nextgen_schedule_css
        cards = response.css(css['card'])

        month_days = [parse_month_day(self.css_text(card, css['date'])) for card in cards]
        dates = season_dates(month_days, season_year(meta['season']))

        for card, match_date in zip(cards, dates):
            item = self.base_item(TeamScheduleItem(), meta)
            stamp = self.css_text(card, css['home_away']).lower()

            item["date"] = match_date
            item["time"] = format_time(self.css_text(card, css['time']))
            item["opponent"] = clean_opponent(self.css_text(card, css['opponent']))
            item["home_away"] = stamp == 'at' and 'away' or stamp == 'vs' and 'home' or ''
            item["location"] = self.css_first(card, css['location'])
            item["result"], item["score"] = split_result(self.css_text(card, css['result']))
            item["image_url"] = card.css(css['image_url']).get() or ''

            yield item

    def parse_coaches_page(self, response):
        meta = {**response.meta, 'season': self.page_season(response)}

        for table in response.css('table'):
            headings = [clean(" ".join(th.css('::text').getall())).lower() for th in table.css('thead th')]
            if 'name' not in headings or 'title' not in headings:
                continue

            for row in table.css('tbody tr'):
                cells = dict(zip(headings, [clean(" ".join(cell.css('::text').getall())) for cell in row.css('td, th')]))
                if not cells.get('name'):
                    continue

                item = self.base_item(PlayerItem(), meta)

                item["name"] = cells['name']
                item["first_name"], item["last_name"] = self.player_first_last_names(item["name"])
                item["title"] = cells.get('title')
                item["profile_url"] = self.absolute_url(row.css('a[href*="/coaches/"]::attr(href), a[href*="/staff/"]::attr(href)').get())
                item["is_athlete"], item["is_coach"] = 0, 1

                yield item

    def embedded_json(self, response, pattern, anchor=''):
        text = response.text
        start = anchor and text.find(anchor) or 0
        match = re.compile(pattern).search(text, max(start, 0))
        if not match:
            return None

        try:
            return json.JSONDecoder().raw_decode(text, match.end())[0]
        except ValueError:
            return None

    def profile_url(self, meta, path, name, profile_id):
        return profile_id and self.BASE_URL.format(f"/sports/{meta['slug']}/{path}/{slugify(name)}/{profile_id}") or ''

    def roster_section_gender(self, player):
        "sidearm-m-roster"
        section = player.xpath('preceding::*[@id="sidearm-m-roster" or @id="sidearm-f-roster"][1]/@id').get() or ''
        gender = re.findall(r'sidearm-(m|f)-roster', section)
        return gender and gender[0] or ''

    def schedule_home_away(self, classes):
        "sidearm-schedule-game sidearm-schedule-away-game"
        venue = re.findall(r'sidearm-schedule-(home|away|neutral)-game', classes or '')
        return venue and venue[0] or ''

    def image_url(self, url):
        "...Adams__Josiah_S1EG6.jpg?width=80&quality=90"
        "https://images.sidearmdev.com/crop?url=https%3A%2F%2F...jpg&width=100"
        proxied = re.findall(r'images\.sidearmdev\.com/[^?]*\?(?:.*&)?url=([^&]+)', url or '')
        if proxied:
            return unquote(proxied[0])

        return self.absolute_url((url or '').split('?')[0])

    def css_first(self, selector, css):
        return next(iter(text for text in clean(selector.css(css).getall()) if text), '')

    def css_last(self, selector, css):
        texts = [text for text in clean(selector.css(css).getall()) if text]
        return texts and texts[-1] or ''


class SidearmLegacyCrawler(BaseCrawler):
    parser_class = SidearmLegacyParser
    start_path = '/services/adaptive_components.ashx?type=main-navigation&count=10&start=0&extra=%7B%7D'

    async def crawl(self):
        page = await self.get(self.BASE_URL.format(self.start_path), api=True)

        sports = {}
        for item in self.nav_sports(self.load_json(page) or []):
            sport = self.sport_links(item)
            if sport and sport['slug'] not in sports:
                sports[sport['slug']] = sport

        # Nav isn't always called Sports, fall back to the roster links on the homepage
        if not sports:
            page = await self.start(self.BASE_URL.format('/'))
            sports = self.homepage_sports(page)

        await self.gather(*self.sport_tasks(page, sports.values()))

    def homepage_sports(self, page):
        sports = {}
        for url, text in self.links(page, r'/sports/[^/]+/roster/?$'):
            slug = re.findall(r'/sports/([^/]+)/roster', url)[0]
            sports[slug] = {
                'slug': slug,
                'sports_name': text or slug.replace('-', ' ').title(),
                'roster_url': url,
                'schedule_url': url.replace('/roster', '/schedule'),
            }

        return sports

    def sport_tasks(self, page, sports):
        tasks = []
        for sport in sports:
            meta = {
                'sports_name': sport['sports_name'],
                'slug': sport['slug'],
                'gender': sports_gender(sport['sports_name']),
            }

            if not self.wants_sport(meta['sports_name'], meta['slug'], meta['gender']):
                continue

            if self.wants('players', 'coaches') and sport.get('roster_url') and self.same_site(sport['roster_url'], page):
                tasks.append(self.crawl_roster(page.urljoin(sport['roster_url']), meta))

            if self.wants('schedules') and sport.get('schedule_url') and self.same_site(sport['schedule_url'], page):
                tasks.append(self.crawl_schedule(page.urljoin(sport['schedule_url']), meta))

        return tasks

    def nav_sports(self, nav):
        for category in nav:
            title = (category.get('title') or '').lower()
            if 'sport' in title or 'team' in title:
                yield from self.nav_items(category.get('items') or [])

    def nav_items(self, items):
        for item in items:
            yield item
            yield from self.nav_items(item.get('items') or [])

    def sport_links(self, item):
        links = {clean(link.get('title') or '').lower(): link.get('url') for link in item.get('schedule_roster_news_links') or []}
        path = re.sub(r'\?.*', '', item.get('url') or '').rstrip('/')

        roster_url = links.get('roster') or (re.search(r'/sports/[^/]+$', path) and f'{path}/roster')
        schedule_url = links.get('schedule') or (re.search(r'/sports/[^/]+$', path) and f'{path}/schedule')

        slug = re.findall(r'/sports/([^/?]+)', roster_url or schedule_url or '')
        if not slug:
            return None

        return {
            'slug': slug[0],
            'sports_name': clean((item.get('sport') or {}).get('title')) or self.slug_name(slug[0]) or clean(item.get('title')),
            'roster_url': roster_url,
            'schedule_url': schedule_url,
        }

    def slug_name(self, slug):
        "mens-basketball"
        gender = re.findall(r'^(mens|womens)-(.+)$', slug)
        if not gender:
            return ''

        prefix, sport = gender[0]
        return f"{prefix[:-1].title()}'s {sport.replace('-', ' ').title()}"

    async def crawl_roster(self, url, meta):
        page = await self.get(url, meta)
        if not page:
            return

        items = list(self.parser.parse_roster(page))
        self.keep(items)

        # Some schools keep coaches on their own page
        if self.wants('coaches') and not any(item.get('is_coach') for item in items):
            page = await self.get(re.sub(r'/roster/?$', '/coaches', page.url.split('?')[0]), self.sport_meta(page))
            if page:
                self.keep(self.parser.parse_coaches_page(page))

    async def crawl_schedule(self, url, meta):
        page = await self.get(url, meta)
        if page:
            self.keep(self.parser.parse_schedule(page))
