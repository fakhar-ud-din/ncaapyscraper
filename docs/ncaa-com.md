# ncaa.com (unofficial)

ncaa.com has scores, box scores, rankings, standings and stat leaders for every school, not just the ones on SIDEARM or WMT. Scores and box scores come from a GraphQL API, the rest are plain HTML tables.

Nothing here is official and any of it can change.

- [GraphQL queries](#graphql-queries)
- [Scoreboard](#scoreboard)
- [Box score](#box-score)
- [Rankings](#rankings)
- [Standings](#standings)
- [Stat leaders](#stat-leaders)
- [Gotchas](#gotchas)


## GraphQL queries

The site's own pages call `https://sdataprod.ncaa.com/` with persisted queries. You don't send the query, only its name and the sha256 hash of it.

```
GET https://sdataprod.ncaa.com/?meta=<name>&extensions={"persistedQuery":{"version":1,"sha256Hash":"<hash>"}}&variables=<json>
```

No key or cookies needed. The hashes change when ncaa.com deploys, an old one gets back

```json
{"errors": [{"message": "PersistedQueryNotFound", "extensions": {"code": "PERSISTED_QUERY_NOT_FOUND"}}]}
```

Every ncaa.com page has the current hashes in its settings JSON, `<script type="application/json" data-drupal-selector="drupal-settings-json">`.

| Where | Hashes |
| --- | --- |
| `scoreboardWidget.shas` on any page | `GetContests_web` |
| `gamecenter.gqlShas` on a game page, `/game/<id>` | Box score, play by play, team stats and scoring summary per sport |


## Scoreboard

`GetContests_web`, every game for a sport, division and day.

```json
{"sportCode": "MBB", "division": 1, "seasonYear": 2026, "contestDate": "11/07/2026", "week": null}
```

Football goes by week instead of day

```json
{"sportCode": "MFB", "division": 11, "seasonYear": 2026, "contestDate": null, "week": 10}
```

| Sport | Code | Sport | Code |
| --- | --- | --- | --- |
| Football | `MFB` | Men's soccer | `MSO` |
| Men's basketball | `MBB` | Women's soccer | `WSO` |
| Women's basketball | `WBB` | Men's ice hockey | `MIH` |
| Baseball | `MBA` | Women's ice hockey | `WIH` |
| Softball | `WSB` | Men's lacrosse | `MLA` |
| Women's volleyball | `WVB` | Women's lacrosse | `WLA` |
| Men's volleyball | `MVB` | Field hockey | `WFH` |
| Beach volleyball | `WSV` | | |

- `division` is a number, `1`, `2`, `3`, `11` for FBS and `12` for FCS. Sports with one national championship for D1 and D2 (men's volleyball, beach volleyball, women's ice hockey) use `0` for what the site calls d1
- `seasonYear` is the year the season started. A May softball game is in the 2025 season if it's May 2026
- The current football week is `scoreboard.currentDate.week` in the settings of `/scoreboard/football/fbs`

Each game has `contestId`, `gameState` (`P` scheduled, `I` live, `F` final), `startDate` (`MM/DD/YYYY`), `startTime` (24h US Eastern), `startTimeEpoch`, `hasStartTime` and two `teams` with `isHome`, `nameShort`, `seoname`, `score`, `teamRank`, `seed`, `isWinner` and `conferenceSeo`.


## Box score

One query per sport, `NCAA_GetGamecenterBoxscore<Sport>ById_web` with `Sport` one of `Football`, `Basketball`, `Baseball`, `Softball`, `Volleyball`, `Soccer`, `Icehockey`, `Lacrosse` or `Fieldhockey`.

```json
{"contestId": "6640609", "staticTestEnv": null}
```

`data.boxscore.teamBoxscore` has a `playerStats` list and `teamStats` per team. The fields depend on the sport.

- Football lists a player once per category (`passing`, `rushing`, `receiving`, `kicking`, `punting`, `kickReturn`, `defense`), the field names don't clash so they can be merged into one row
- Baseball and softball nest `batterStats`, `pitcherStats` and `fieldStats`, soccer nests `penalties` and `goalTypes`
- Numbers come back as strings, `"34"` and `".000"`
- Smaller D2 and D3 games often have an empty `playerStats`


## Rankings

`https://www.ncaa.com/rankings/<sport>/<division>/<poll>`, e.g. `/rankings/football/fbs/associated-press`. Leave out the poll for the default one. The polls are the options of `#edit-rankings-menu`, the date is in `.rankings-last-updated`. It's one HTML table, the school column has first place votes in brackets, `Georgia (53)`.


## Standings

`https://www.ncaa.com/standings/<sport>/<division>`. Each conference is a `figure.standings-conference` followed by a `.table-wrap` with its table. The header has a group row (`School`, `Conference`, `Overall`) and a row under it (`W`, `L`, `PCT`...). Don't trust `colspan` on the group row, every group starts again with `W`.

Only football and basketball have standings, the page for other sports loads but has no tables.


## Stat leaders

`https://www.ncaa.com/stats/<sport>/<division>` lists every stat in `#select-container-individual` and `#select-container-team`. Each option's value is the url of that stat.

```
https://www.ncaa.com/stats/football/fbs/current/individual/469
https://www.ncaa.com/stats/football/fbs/current/individual/469/p2
```

50 rows a page in `.block-stats__stats-table`, the stat name is in `.stats-header__lower__title`. Tied players show `-` instead of a rank, even at the top of a page.


## Gotchas

- The GraphQL server only finds the hash in compact JSON. `{"version": 1, ...}` with a space after the colon is a 500 with "Must specify sha256Hash"
- The older `data.ncaa.com/casablanca/...scoreboard.json` and `boxscore.json` files are gone, they 404
- Sport urls are `basketball-men`, `soccer-women`, `icehockey-men`, `fieldhockey`. ncaapyscraper takes `mens-basketball` style names and maps them
- It's one site for everything, so go easy, a couple of requests a second is plenty
