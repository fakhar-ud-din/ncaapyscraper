# Docs

Notes on the platforms college athletics sites are built on, and the JSON and pages you can read data from. Useful whether you use ncaapyscraper or write your own.

None of this is official. These are the endpoints the websites call themselves, they're not documented and can change without notice.

| Page | What's in it |
| --- | --- |
| [SIDEARM API](sidearm-api.md) | `/api/v2/` on newer SIDEARM sites. Sports, rosters, schedules, coaches |
| [WMT API](wmt-api.md) | `/website-api/` on WMT Digital sites. Same data, JSON:API style queries |
| [Older SIDEARM sites](sidearm-classic.md) | The `.aspx` sites most D2 and D3 schools are on. Navigation JSON plus roster and schedule pages |
| [ncaa.com](ncaa-com.md) | Scoreboards and box scores from its GraphQL API, plus rankings, standings and stat leaders pages |
| [Supported schools](schools.md) | Every school this project covers, by division and conference |


## Which platform is a site on?

Try these in order, the first one that returns JSON wins.

| Check | Platform |
| --- | --- |
| `https://<site>/api/v2/Sports` | SIDEARM API |
| `https://<site>/website-api/sports` | WMT |
| `https://<site>/services/adaptive_components.ashx?type=main-navigation&count=10&start=0&extra=%7B%7D` | Older SIDEARM |

If none of them answer, the site is on something else (PrestoSports, a custom build, plain WordPress). Kentucky, South Carolina and Arkansas are older WMT WordPress sites, those are read straight from their roster tables and schedule pages.


## Domains move

Schools rebrand their athletics sites more often than you'd think (`texassports.com` is now `texaslonghorns.com`). The old domain usually redirects, so follow redirects and don't lock your scraper to one hostname. The API host can also differ from the website, Arizona State's site is `sundevils.com` but its API only answers on `thesundevils.com`.


## Being nice

These are school websites. Keep it to a few requests a second per site, cache what you can, and don't hammer them on game days.
