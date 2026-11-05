# Older SIDEARM sites (unofficial)

Most college athletics sites, especially Division II and III, still run the older SIDEARM platform. You can spot them by the `.aspx` pages and urls like `/sports/football/roster`. They don't have the `/api/v2/` API, but they do have a JSON navigation service and very consistent roster and schedule pages.

Nothing here is official and any of it can change.

**Is a site on it?** If `https://<site>/api/v2/Sports` gives a 404 but this returns JSON, it is:

```bash
curl "https://villanova.com/services/adaptive_components.ashx?type=main-navigation&count=10&start=0&extra=%7B%7D"
```

- [Sports list](#sports-list)
- [Roster page](#roster-page)
- [Coaches page](#coaches-page)
- [Schedule page](#schedule-page)
- [Vue template](#vue-template)
- [Other services](#other-services)


## Sports list

`GET /services/adaptive_components.ashx?type=main-navigation&count=10&start=0&extra=%7B%7D`

The site's main menu as JSON. Find the category whose title has "Sports" or "Teams" in it, every item under it is a sport.

```json
[
  {
    "title": "Sports",
    "items": [
      {
        "title": "Basketball",
        "url": "/sports/mens-basketball",
        "sport": { "title": "Men's Basketball", "global_sport_name_slug": "mens-basketball", "gender": null },
        "schedule_roster_news_links": [
          { "title": "Schedule", "url": "/sports/mens-basketball/schedule" },
          { "title": "Roster", "url": "/sports/mens-basketball/roster" },
          { "title": "News", "url": "/sports/mens-basketball/archives" }
        ]
      }
    ]
  }
]
```

- Item `title` is the short menu label ("Basketball"), use `sport.title` for the real name
- Some menus leave `schedule_roster_news_links` empty, the roster is still at `{url}/roster`
- Items can be nested and the same sport can be listed twice (swimming under men's and women's)


## Roster page

`GET /sports/{slug}/roster`

Server rendered HTML, one `li.sidearm-roster-player` per athlete.

| Selector | Field |
| --- | --- |
| `li.sidearm-roster-player` | One athlete, `data-player-url` is the profile link |
| `.sidearm-roster-player-name h3` | Name |
| `.sidearm-roster-player-jersey-number` | Number |
| `.sidearm-roster-player-position .text-bold` | Position |
| `.sidearm-roster-player-height` | Height, like `6'0"` |
| `.sidearm-roster-player-weight` | Weight, like `165 lbs` |
| `.sidearm-roster-player-academic-year` | Class. Appears twice, short (`Fr.`) then long (`Freshman`) |
| `.sidearm-roster-player-hometown` | Hometown (also appears twice) |
| `.sidearm-roster-player-highschool` | High school |
| `.sidearm-roster-player-previous-school` | Previous school |
| `.sidearm-roster-player-image img` | Headshot in `data-src` (lazy loaded) |
| `li.sidearm-roster-coach` | One coach, with `.sidearm-roster-coach-name` and `.sidearm-roster-coach-title` |

Combined rosters (track, swimming) split men and women under `#sidearm-m-roster` and `#sidearm-f-roster`.

The same page also has a table view (`table.sidearm-table`) with cleaner values like `6-0` and `165`, if you'd rather parse tables.


## Coaches page

`GET /sports/{slug}/coaches`

Some schools don't put coaches on the roster page. They're here instead, in a table with `Name` and `Title` columns.


## Schedule page

`GET /sports/{slug}/schedule`

One `li.sidearm-schedule-game` per game, and a JSON-LD block with every game's start time.

| Selector | Field |
| --- | --- |
| `li.sidearm-schedule-game` | One game. Class has `sidearm-schedule-home-game`, `-away-game` or `-neutral-game` |
| `.sidearm-schedule-game-opponent-date span` | Date and time text, `Aug 28 (Fri)`, `6:00 PM` |
| `.sidearm-schedule-game-opponent-name` | Opponent |
| `.sidearm-schedule-game-location span` | Location, venue is in the second span |
| `.sidearm-schedule-game-conference` | Present for conference games |
| `.sidearm-schedule-game-result` | `W, 17-16`, school's score first |
| `.sidearm-schedule-game-coverage-tv-content` | TV |
| `.sidearm-schedule-game-opponent-logo img` | Opponent logo in `data-src` |

The dates on the cards don't have a year. The page also has `<script type="application/ld+json">` with an array of `SportsEvent` objects in the same order as the cards, each with a full `startDate` like `2026-08-28T18:00:00`. Match them up by position.


## Vue template

A handful of schools are on a newer SIDEARM template where the page is rendered in the browser. The HTML has no `li` cards, but the data is right there in the page:

- Roster page: `roster: {...}` inside the `#vue-rosters` script. Same fields as the [SIDEARM API](sidearm-api.md) roster, just snake_case (`first_name`, `jersey_number`, `height_feet`, `academic_year_long`, `rp_id`)
- Schedule page: `"games":[...]` in the script after `var schedule_id`. Same shape as the API schedule (`date`, `time`, `location_indicator`, `opponent.title`, `result.team_score`)


## Other services

Seen on these sites, not used in this project.

| Endpoint | What it is |
| --- | --- |
| `/services/responsive-schedule.ashx?game_id={id}&opponent_id={id}&sport_id={id}` | One game's details (box score, leaders) |
| `/services/responsive-roster.ashx?player_id={id}&sport_id={id}&sport_shortname={short}&year={year}` | One player's stats |
| `/services/schedule_txt.ashx?schedule={id}` | Plain text schedule |
