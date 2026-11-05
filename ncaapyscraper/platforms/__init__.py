from ncaapyscraper.platforms.sidearm import SidearmCrawler
from ncaapyscraper.platforms.sidearm_legacy import SidearmLegacyCrawler
from ncaapyscraper.platforms.wmt import WmtCrawler
from ncaapyscraper.platforms.wordpress import WordpressCrawler


PLATFORMS = {
    'sidearm': SidearmCrawler,
    'sidearm_legacy': SidearmLegacyCrawler,
    'wmt': WmtCrawler,
    'wordpress': WordpressCrawler,
}
