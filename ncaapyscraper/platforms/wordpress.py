import re

from ncaapyscraper.constants import *
from ncaapyscraper.items import PlayerItem, TeamScheduleItem
from ncaapyscraper.platforms.base import BaseParser, BaseCrawler
from ncaapyscraper.utils import (
    clean,
    sports_gender,
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
    roster_table_css_v1,
    schedule_css_v1,
)


class WordpressParser(BaseParser):
    roster_css = roster_table_css_v1
    schedule_css = schedule_css_v1

    gender_map = {
        'M': "Men's",
        'W': "Women's",
    }

    def parse_roster(self, response):
        meta = self.page_meta(response, self.roster_css)

        for table in response.css(self.roster_css['players']):
            table_meta = {**meta, 'gender': self.table_gender(table) or meta['gender']}

            for row in self.table_rows(table):
                item = self.base_item(PlayerItem(), table_meta)

                item["sport_gender"] = meta['gender']
                item["name"] = row.get('name') or ''
                item["first_name"], item["last_name"] = self.player_first_last_names(item["name"])
                item["shirt_no"] = row.get('shirt_no')
                item["position"] = row.get('position')
                item["height"] = row.get('height')
                item["weight"] = format_weight(row.get('weight'))
                item["player_class"] = row.get('player_class')
                item["hometown"] = self.player_hometown(row)
                item["highschool"], item["previous_school"] = self.player_schools(row)
                item["major"] = row.get('major')
                item["profile_url"] = self.absolute_url(row.get('profile_url'))
                item["is_athlete"], item["is_coach"] = 1, 0

                yield item

        for table in response.css(self.roster_css['coaches']):
            for row in self.table_rows(table):
                item = self.base_item(PlayerItem(), meta)

                item["name"] = row.get('name') or ''
                item["first_name"], item["last_name"] = self.player_first_last_names(item["name"])
                item["title"] = row.get('position')
                item["profile_url"] = self.absolute_url(row.get('profile_url'))
                item["is_athlete"], item["is_coach"] = 0, 1

                yield item

    def parse_schedule(self, response):
        css = self.schedule_css
        meta = self.page_meta(response, css)

        cards = [card for card in response.css(css['card']) if self.css_text(card, css['opponent'])]
        events = self.schedule_events(response)

        if len(events) != len(cards):
            month_days = [parse_month_day(self.css_text(card, css['date'])) for card in cards]
            events = [(match_date, '') for match_date in season_dates(month_days, season_year(meta['season']))]

        for card, (match_date, event_time) in zip(cards, events):
            item = self.base_item(TeamScheduleItem(), meta)
            result = self.css_text(card, css['result'])
            match_time = self.css_text(card, css['time'])

            if is_time(result):
                match_time, result = match_time or result, ''

            item["date"] = match_date
            item["time"] = format_time(match_time or event_time)
            item["opponent"] = clean_opponent(self.css_text(card, css['opponent']))
            item["home_away"] = self.schedule_home_away(self.css_text(card, css['home_away']))
            item["venue"], item["location"] = self.schedule_location(self.css_text(card, css['location']))
            item["result"], item["score"] = split_result(result, self.css_text(card, css['score']))
            item["image_url"] = self.absolute_url((card.css(css['image_url']).getall() or [''])[-1])

            yield item

    def schedule_location(self, location):
        "Rupp Arena at Central Bank Center | Lexington, Ky."
        if ' | ' in (location or ''):
            venue, location = location.rsplit(' | ', 1)
            return clean(venue), clean(location)

        return '', location

    def page_meta(self, response, css):
        sports_name = next(iter(name for name in clean(response.css(css['sports_name']).getall()) if name), '')

        gender = re.findall(r'\((M|W)\)', sports_name)
        if gender:
            sports_name = f"{self.gender_map[gender[0]]} {clean(re.sub(r'[(](M|W)[)]', '', sports_name))}"

        return {
            'sports_name': sports_name,
            'gender': sports_gender(sports_name) or self.url_gender(response.url),
            'season': self.page_season(response),
        }

    def url_gender(self, url):
        "/sport/w-volley/roster/"
        gender = re.findall(r'/sport/(m|w)-', url)
        return gender and GENDER_MAP[gender[0]] or ''

    def table_gender(self, table):
        "players-table__women"
        gender = re.findall(r'__(men|women)$', table.xpath('@id').get() or '')
        return gender and gender[0] or ''

    def schedule_home_away(self, text):
        "schedule__item schedule-item home"
        for venue in ['home', 'away', 'neutral']:
            if venue in (text or '').lower().split():
                return venue

        return ''


class WordpressCrawler(BaseCrawler):
    parser_class = WordpressParser

    async def crawl(self):
        page = await self.start(self.BASE_URL.format('/'))

        tasks = []
        if self.wants('players', 'coaches'):
            tasks += [self.crawl_page(url, self.parser.parse_roster) for url, _ in self.links(page, r'/sports?/[^/]+/roster/?$')]

        if self.wants('schedules'):
            tasks += [self.crawl_page(url, self.parser.parse_schedule) for url, _ in self.links(page, r'/sports?/[^/]+/schedule/?$')]

        await self.gather(*tasks)

    # Sport names only show up on the page here, so the --sport filter runs on the items
    async def crawl_page(self, url, parse):
        page = await self.get(url)
        if page:
            self.keep(parse(page), check_sport=True)
