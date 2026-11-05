# ncaapyscraper

Rosters, coaches and schedules for every sport at almost 1,000 NCAA schools, from Division I down to Division III. Use it from the command line or from Python, and you get clean JSON back.

```bash
pip install ncaapyscraper
```

```python
import ncaapyscraper as nps

nps.get_roster("duke", "football")
nps.get_schedule("alabama", "mens-basketball")
```

Don't want to run anything? A fresh copy of all of it is published every week, see [Download the data](#download-the-data).


## Download the data

Every Monday a GitHub Action scrapes every supported school and publishes the result under [Releases](https://github.com/fakhar-ud-din/ncaapyscraper/releases).

- [ncaapyscraper-data.zip](https://github.com/fakhar-ud-din/ncaapyscraper/releases/latest/download/ncaapyscraper-data.zip) has one JSON file per school plus `index.json`
- [index.json](https://github.com/fakhar-ud-din/ncaapyscraper/releases/latest/download/index.json) on its own lists every school with its conference, division and file name

Bios are left out of the weekly data to keep it small. Run it yourself if you need them.


## Command line

One school, everything

```bash
ncaapyscraper duke
```

A few schools, by key or by website

```bash
ncaapyscraper alabama navy goduke.com
```

Football only

```bash
ncaapyscraper ohio_state --sport football
```

Basketball schedules for the whole SEC (`basketball` matches men's and women's)

```bash
ncaapyscraper --conference sec --sport basketball --schedules
```

Every FCS school, athletes only

```bash
ncaapyscraper --division fcs --players
```

Women's soccer rosters across Division III, no bios

```bash
ncaapyscraper --division 3 --sport womens-soccer --players --no-bios
```

Find a school's key, or see what's in a conference

```bash
ncaapyscraper --list -c "big sky"
ncaapyscraper --conferences
```

Each school is saved to `output/<key>.json`. Pick another folder with `-o`.

| Flag | What it does |
| --- | --- |
| `-l`, `--list` | List supported schools. Combine with `-c` or `-d` |
| `--conferences` | List conferences |
| `-a`, `--all` | Every supported school |
| `-c`, `--conference` | Every school in a conference. Short names work: `sec`, `acc`, `big10`, `big12`, `ivy`, `mwc`, `a10`... or any part of the name |
| `-d`, `--division` | `1`, `2`, `3`, `fbs` or `fcs` |
| `-s`, `--sport` | Only these sports, e.g. `football`, `mens-basketball`, `golf`. Repeat it or use commas |
| `-g`, `--gender` | `men` or `women`. Co-ed teams (track, swimming, rifle) stay in, their athletes get filtered |
| `--players` | Athletes only |
| `--coaches` | Coaches and staff only |
| `--schedules` | Schedules only |
| `--no-bios` | Leave out bios, files get a lot smaller |
| `--compact` | JSON without indentation |
| `-o`, `--output` | Output folder, default `output` |
| `-p`, `--parallel` | Schools to scrape at once, default `4` |
| `-v`, `--verbose` | Log every request |

`--players`, `--coaches` and `--schedules` can be combined. Without any of them you get all three.


## Python

The `get_` functions return plain lists of dicts, one row per player, coach or game, with `school`, `sport` and `season` on every row.

```python
import ncaapyscraper as nps

roster = nps.get_roster("duke", "football")
coaches = nps.get_coaches("navy", "football")
games = nps.get_schedule("stanford", "basketball")      # men's and women's

school = nps.get_school("villanova", sports=["football"], data=["players", "schedules"])

nps.list_schools("sec")                                 # or division="fbs", 1, 2, 3
```

Straight into pandas

```python
import pandas as pd

df = pd.DataFrame(nps.get_roster("texas", "baseball"))
```

They work in Jupyter too.

For lots of schools at once there's an async version. It keeps every school's site to a few requests at a time, and yields each school as it finishes.

```python
import asyncio
import ncaapyscraper as nps

async def main():
    keys = [school["key"] for school in nps.list_schools("ivy")]

    async for key, result in nps.fetch_schools(keys, sports="football", parallel=8):
        if isinstance(result, Exception):
            print(key, "failed", result)
            continue

        print(key, sum(len(sport["players"]) for sport in result["sports"]))

asyncio.run(main())
```

`fetch_school`, `fetch_roster`, `fetch_coaches` and `fetch_schedule` are the async versions of the `get_` functions.

A school that isn't on the list yet? Pass a dict instead of a key.

```python
nps.get_school({"name": "Boise State University", "site": "broncosports.com", "platform": "sidearm"})
```


## JSON response

One file (or dict) per school, grouped by sport. Missing values are `null`.

```json
{
  "key": "duke",
  "school": "Duke University",
  "conference": "Atlantic Coast Conference",
  "division": 1,
  "subdivision": "FBS",
  "state": "NC",
  "site": "https://goduke.com",
  "platform": "sidearm",
  "scraped_at": "2026-11-05T07:29:39Z",
  "sports": [
    {
      "sport": "Football",
      "gender": "men",
      "season": "2026",
      "players": [
        {
          "name": "Jordan Smith",
          "first_name": "Jordan",
          "last_name": "Smith",
          "shirt_no": "24",
          "position": "RB",
          "height": "5-10",
          "weight": 205,
          "player_class": "Senior",
          "hometown": "Charlotte, N.C.",
          "highschool": "Myers Park",
          "previous_school": "East Carolina",
          "major": "Economics",
          "gender": "men",
          "image_url": "https://goduke.com/images/2026/7/27/smith_jordan.jpg",
          "profile_url": "https://goduke.com/sports/football/roster/jordan-smith/24470",
          "bio": null
        }
      ],
      "coaches": [
        {
          "name": "Chris Allen",
          "first_name": "Chris",
          "last_name": "Allen",
          "title": "Head Coach",
          "image_url": "https://goduke.com/images/2024/3/6/allen_chris.jpg",
          "profile_url": "https://goduke.com/sports/football/roster/coaches/chris-allen/5388",
          "bio": "Chris Allen was named head coach in December 2023..."
        }
      ],
      "schedule": [
        {
          "date": "2026-09-05",
          "time": "5:00 PM",
          "datetime_utc": "2026-09-05T21:00:00Z",
          "opponent": "Tulane",
          "home_away": "home",
          "location": "Durham, N.C.",
          "venue": "Brooks Field at Wallace Wade Stadium",
          "is_conference": false,
          "result": "W",
          "score": "17-3",
          "tournament": null,
          "tv": "ACC Network",
          "image_url": "https://goduke.com/images/logos/Tulane-Wave.png"
        }
      ]
    }
  ]
}
```

- `coaches` includes support staff, `title` tells you who's who
- `date` and `time` are the school's local time. `datetime_utc` is filled for schools on the SIDEARM API and WMT
- `score` is always the school's score first, `result` is `W`, `L` or `T`
- `gender` on a player only matters for co-ed teams like track and swimming
- `subdivision` is `FBS`, `FCS` or `null`
- How much detail you get depends on what the school puts on its site. Bios, majors and weights are often missing for smaller schools
- With `--players`, `--coaches` or `--schedules` you only get those keys in each sport


## Supported schools

Every NCAA school whose athletics site runs on SIDEARM Sports or WMT Digital, which is most of them. The full list with keys is in [docs/schools.md](docs/schools.md), or run `ncaapyscraper --list`.

Schools on other platforms (PrestoSports and custom builds) aren't covered yet.


## Docs

The [docs](docs/README.md) folder is an unofficial reference for the APIs and pages these sites use, handy even if you write your own scraper.

- [SIDEARM API](docs/sidearm-api.md)
- [WMT API](docs/wmt-api.md)
- [Older SIDEARM sites](docs/sidearm-classic.md)


## Adding a new school

NAIA, junior colleges and anything else on the same platforms work too.

1. Find the school's athletics website
2. Open these in the browser, the first one that shows JSON tells you the platform
   - `https://<site>/api/v2/Sports` → `sidearm`
   - `https://<site>/website-api/sports` → `wmt`
   - `https://<site>/services/adaptive_components.ashx?type=main-navigation&count=10&start=0&extra=%7B%7D` → `sidearm_legacy`
3. Try it straight away by passing a dict to `get_school` (see [Python](#python))
4. To add it for everyone, add a row to [ncaapyscraper/schools.csv](ncaapyscraper/schools.csv) and open a PR

```csv
key,name,conference,division,subdivision,state,site,platform
my_school,My School University,My Conference,3,,OH,myschoolathletics.com,sidearm_legacy
```


## Development

1. Clone the repo and go into the folder
2. Run `python3 -m venv env` and `source env/bin/activate`
3. Run `pip install -e ".[dev]"`
4. Run `pytest`

Needs Python 3.10+.


## License

MIT
