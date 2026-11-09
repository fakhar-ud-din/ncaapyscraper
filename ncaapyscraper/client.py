import asyncio
import json
import logging
import random
import time

from urllib.parse import urljoin, urlparse

import httpx
from parsel import Selector

from ncaapyscraper.useragents import MY_USER_AGENTS


logger = logging.getLogger('ncaapyscraper')

RETRY_STATUS = [408, 429, 500, 502, 503, 504, 520, 522, 524]


class Page:
    "What the parsers work on, a response with url, text, meta and css / xpath selectors"

    def __init__(self, url, status, text, meta=None):
        self.url = url
        self.status = status
        self.text = text or ''
        self.meta = meta or {}
        self._selector = None

    @property
    def selector(self):
        if self._selector is None:
            self._selector = Selector(text=self.text or '<html></html>')

        return self._selector

    def css(self, query):
        return self.selector.css(query)

    def xpath(self, query):
        return self.selector.xpath(query)

    def json(self):
        return json.loads(self.text)

    def urljoin(self, url):
        return urljoin(self.url, url)


class Fetcher:
    "One http client for everything, keeps each school site to a few requests at a time"

    def __init__(self, per_site=4, delay=.5, timeout=30, retries=2):
        self.per_site = per_site
        self.delay = delay
        self.retries = retries

        self.client = httpx.AsyncClient(
            follow_redirects=True,
            timeout=timeout,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        )
        self.slots = {}
        self.locks = {}
        self.last_request = {}
        self.failures = {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()

    async def close(self):
        await self.client.aclose()

    def slot(self, host):
        if host not in self.slots:
            self.slots[host] = asyncio.Semaphore(self.per_site)
            self.locks[host] = asyncio.Lock()

        return self.slots[host]

    async def wait_turn(self, host):
        async with self.locks[host]:
            gap = self.delay - (time.monotonic() - self.last_request.get(host, 0))
            if gap > 0:
                await asyncio.sleep(gap)

            self.last_request[host] = time.monotonic()

    async def get(self, url, headers=None, meta=None):
        host = urlparse(url).hostname or ''
        headers = {'User-Agent': random.choice(MY_USER_AGENTS), **(headers or {})}
        response = None
        error = None

        async with self.slot(host):
            for attempt in range(self.retries + 1):
                await self.wait_turn(host)

                try:
                    response = await self.client.get(url, headers=headers)
                except httpx.HTTPError as e:
                    logger.debug(f'Failed {url}: {e!r}')
                    response, error = None, e
                else:
                    logger.debug(f'Crawled ({response.status_code}) {response.url}')
                    if response.status_code not in RETRY_STATUS:
                        break

                if attempt < self.retries:
                    await asyncio.sleep(2 ** attempt)

        if response is None or response.status_code >= 400:
            # Kept so "couldn't load" can say why, a 403 and a timeout need different fixes
            self.failures[url] = f'status {response.status_code}' if response is not None else type(error).__name__
            return None

        return Page(str(response.url), response.status_code, response.text, meta)

    async def get_or_fail(self, url, headers=None, meta=None):
        "Same as get, but raises when the page couldn't be loaded"
        page = await self.get(url, headers=headers, meta=meta)
        if not page:
            raise ConnectionError(f"Couldn't load {url} ({self.failures.get(url, 'no response')})")

        return page
