import asyncio
import json
import logging
import re

from datetime import datetime
from urllib.parse import urlparse

from ncaapyscraper.constants import *
from ncaapyscraper.items import TeamScheduleItem
from ncaapyscraper.utils import clean, clean_value, sport_key, split_arg


logger = logging.getLogger('ncaapyscraper')


class BaseParser:
    BASE_URL = ''
    SCHOOL_NAME = ''
    CONFERENCE_NAME = ''

    def __init__(self, school):
        self.BASE_URL = f"https://{school['site']}{{}}"
        self.SCHOOL_NAME = school['name']
        self.CONFERENCE_NAME = school['conference']

        # Older sites bring their own selectors, see schools.py
        for selectors in ['roster_css', 'schedule_css']:
            if school.get(selectors):
                setattr(self, selectors, school[selectors])

    def base_item(self, item, meta):
        item['school'] = self.SCHOOL_NAME
        item['conference'] = self.CONFERENCE_NAME
        item['sport'] = meta.get('sports_name')
        item['sport_gender'] = meta.get('gender')
        item['gender'] = meta.get('gender')
        item['season'] = meta.get('season')

        return item

    def absolute_url(self, url):
        if not url:
            return ''

        if not urlparse(url).hostname:
            url = self.BASE_URL.format(f"/{url.lstrip('/')}")

        return url

    def player_first_last_names(self, name):
        names = name.split(",")[0].split(" ")
        first_name, last_name = names[0], " ".join(names[1:])
        return first_name, last_name

    def player_gender(self, gender, meta):
        return GENDER_MAP.get((gender or '').lower()) or meta.get('gender') or ''

    def css_text(self, selector, css):
        if not css:
            return ''

        return clean(" ".join(selector.css(css).getall() or []))

    def table_rows(self, table):
        "Ht. -> height, Full Name -> name, Hometown / High School -> hometown/highschool"
        headings = [clean(" ".join(th.css('::text').getall())).lower() for th in table.css('thead th')]
        headings = [TABLE_HEADINGS.get(re.sub(r'\s*/\s*', '/', heading.replace('.', '')).strip(), heading) for heading in headings]

        for row in table.css('tbody tr'):
            data = [clean_value(" ".join(td.css('::text').getall())) for td in row.css('td, th')]
            if not any(data):
                continue

            # Staff tables can have an extra caption cell ("Coaching Staff") in the header row
            row_headings = headings[len(headings) - len(data):] if len(data) < len(headings) else headings
            row_data = {heading: data[idx] for idx, heading in enumerate(row_headings) if idx < len(data)}
            row_data['profile_url'] = row.css('td a::attr(href), th a::attr(href)').get()
            row_data['image_url'] = row.css('img::attr(data-src), img::attr(src)').get()

            yield row_data

    def player_schools(self, row):
        "Hewitt-Trussville HS / Virginia"
        if row.get('highschool/previous_school'):
            schools = [clean(school) for school in row['highschool/previous_school'].split(' / ')]
            return schools[0], len(schools) > 1 and schools[1] or ''

        if row.get('hometown/highschool'):
            schools = [clean(school) for school in row['hometown/highschool'].split(' / ')]
            return len(schools) > 1 and schools[1] or '', row.get('previous_school') or ''

        return row.get('highschool') or '', row.get('previous_school') or ''

    def player_hometown(self, row):
        "Upper Darby, Pa. / Bonner-Prendie"
        if row.get('hometown'):
            return row['hometown']

        return clean((row.get('hometown/highschool') or '').split(' / ')[0])

    def page_season(self, response):
        "Football Roster 2026"
        "2026-27 Men's Basketball Schedule"
        "/sport/m-footbl/roster/?season=2026-27"
        season_re = r'\b(\d{4}(?:-\d{2})?)\b'

        season = re.findall(season_re, response.css('title::text').get() or '')
        if season:
            return season[0]

        seasons = response.css('#seasonSelect option[selected]::attr(value), select[name="season"] option[selected]::attr(value)').getall()
        seasons = seasons or response.css('#seasonSelect option::attr(value), select[name="season"] option::attr(value)').getall()
        season = seasons and re.findall(season_re, seasons[-1]) or []
        return season and season[-1] or ''

    def schedule_events(self, response):
        "2026-09-05T13:00"
        events = []
        for raw in response.css('script[type="application/ld+json"]::text').getall():
            try:
                data = json.loads(raw)
            except ValueError:
                continue

            for event in data if isinstance(data, list) else [data]:
                if not isinstance(event, dict) or event.get('@type') not in ('Event', 'SportsEvent') or not event.get('startDate'):
                    continue

                start_date = event['startDate']
                event_time = start_date[11:16]
                if event_time and event_time != '00:00':
                    event_time = datetime.strptime(event_time, '%H:%M').strftime('%I:%M %p').lstrip('0')

                events.append((start_date[:10], event_time != '00:00' and event_time or ''))

        return events


def bare_host(host):
    return re.sub(r'^www\.', '', (host or '').lower())


class BaseCrawler:
    api_headers = {'Accept': 'application/json'}
    parser_class = BaseParser
    start_path = '/'

    def __init__(self, school, fetcher, sports=None, data=None, gender=None):
        self.school = school
        self.fetcher = fetcher

        # Schools move to new domains all the time, every link check goes through same_site instead
        self.BASE_URL = f"https://{self.school['site']}{{}}"
        self.parser = self.parser_class(self.school)

        self.sports = [sport_key(sport) for sport in split_arg(sports)]
        self.data = split_arg(data) or DATA_TYPES
        self.gender = GENDER_MAP.get((gender or '').lower(), '')
        self.items = []

    async def crawl(self):
        raise NotImplementedError

    async def get(self, url, meta=None, api=False):
        return await self.fetcher.get(url, headers=api and self.api_headers or None, meta=meta)

    async def start(self, url, api=False):
        "First request for a school, if this fails the school failed, not just one sport"
        page = await self.get(url, api=api)
        if not page:
            raise ConnectionError(f"Couldn't load {url}")

        return page

    async def gather(self, *tasks):
        "One sport failing shouldn't take the whole school down"
        for result in await asyncio.gather(*tasks, return_exceptions=True):
            if isinstance(result, Exception):
                logger.warning(f"{self.school['key']}: {result!r}")

    def wants(self, *data_types):
        return any(data_type in self.data for data_type in data_types)

    def wants_sport(self, sports_name, slug='', gender=''):
        "--sport basketball matches Men's Basketball and Women's Basketball"
        if self.gender and gender and gender != self.gender:
            return False

        if not self.sports:
            return True

        keys = [key for key in [sport_key(sports_name), sport_key(slug)] if key]
        return any(key == sport or key.endswith(f'-{sport}') for key in keys for sport in self.sports)

    def keep(self, items, check_sport=False):
        kept = []
        for item in items:
            if self.item_type(item) not in self.data:
                continue

            if self.gender and item.get('gender') not in (self.gender, '', None):
                continue

            if check_sport and not self.wants_sport(item.get('sport'), gender=item.get('sport_gender')):
                continue

            kept.append(item)

        self.items.extend(kept)
        return kept

    def item_type(self, item):
        if isinstance(item, TeamScheduleItem):
            return 'schedules'

        return item.get('is_coach') and 'coaches' or 'players'

    def same_site(self, url, page):
        "Relative links, the school's site, or wherever it redirected to"
        host = urlparse(url).hostname
        sites = {bare_host(self.school['site']), bare_host(urlparse(page.url).hostname)}
        return not host or bare_host(host) in sites

    def links(self, page, pattern):
        "Links on the page matching pattern, absolute and once each"
        found = {}
        for link in page.css('a[href]'):
            # Same page linked as /roster/ and /roster/#coaches is still one page
            url = page.urljoin(link.attrib['href'].strip()).split('#')[0]
            key = url.split('?')[0].rstrip('/')

            if re.search(pattern, url.split('?')[0]) and self.same_site(url, page) and key not in found:
                found[key] = (url, clean(" ".join(link.css('::text').getall())))

        return found.values()

    def load_json(self, page):
        if not page or not page.text:
            return None

        try:
            return page.json()
        except ValueError:
            logger.warning(f'Not a json response: {page.url}')
            return None

    def sport_meta(self, page):
        return {key: page.meta.get(key) for key in META_KEYS}
