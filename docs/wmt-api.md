# WMT Digital API (unofficial)

WMT Digital runs athletics sites for schools like Stanford, Penn State, LSU and Texas A&M. Their sites load data from a JSON API on the same domain under `/website-api/`. No key needed, it's what the website calls.

Nothing here is official and any of it can change.

**Is a site on it?** Open `https://<site>/website-api/sports`. If you get JSON with a `data` array, it is.

```bash
curl "https://gostanford.com/website-api/sports?per_page=100"
```

- [How queries work](#how-queries-work)
- [Site config](#site-config)
- [Sports](#sports)
- [Players on a roster](#players-on-a-roster)
- [Staff on a roster](#staff-on-a-roster)
- [Schedule](#schedule)
- [Other endpoints](#other-endpoints)
- [Gotchas](#gotchas)


## How queries work

It's a JSON:API style backend (Laravel). Every list endpoint takes the same kind of query string:

| Param | Example | Notes |
| --- | --- | --- |
| `filter[...]` | `filter[roster_id]=1779` | Filter on a field |
| `include` | `include=player,classLevel` | Pull related records into the response, comma separated |
| `sort` | `sort=datetime`, `sort=-datetime` | `-` for descending |
| `per_page` | `per_page=100` | Page size |
| `page` | `page=2` | Page number |

Lists come back as `{ "data": [...], "links": {...}, "meta": {...} }`. Keep going while `meta.current_page < meta.last_page`.


## Site config

`GET /website-api/website-config`

Mostly menus and branding. The useful bit is the site's timezone, event times are in UTC and you need this to get the local date right.

```json
{ "data": { "settings": { "website_timezone": "America/Los_Angeles", "site_title": "Stanford Cardinal" } } }
```

The website falls back to `America/New_York` when it's missing.


## Sports

`GET /website-api/sports?per_page=100`

```json
{
  "data": [
    {
      "id": 8,
      "name": "Football",
      "slug": "football",
      "gender": null,
      "default_roster_id": 1779,
      "schedule_id": 1588,
      "default_season_id": 267
    }
  ]
}
```

- `default_roster_id` and `schedule_id` are what you need next
- `gender` is often `null`, the name usually tells you (`Men's Basketball`)
- The list also has non-sports like "Featured" or "Hall of Fame" with no roster or schedule


## Players on a roster

`GET /website-api/player-rosters?filter[roster_id]={rosterId}&include=player,classLevel,playerPosition,photo,roster.season&per_page=100`

One record per player on the roster. Bio details live on the nested `player`, roster-specific stuff (number, height, position) on the outer record.

```json
{
  "data": [
    {
      "id": 18666,
      "jersey_number": 24,
      "jersey_number_label": "24",
      "height_feet": 5,
      "height_inches": 10,
      "weight": 205,
      "is_captain": false,
      "short_biography": null,
      "player_position": { "abbreviation": "RB", "name": "Running Back" },
      "class_level": { "name": "Senior" },
      "photo": { "url": "https://gostanford.com/imgproxy/..." },
      "roster": { "season": { "name": "2026", "slug": "2026" } },
      "player": {
        "first_name": "Jordan",
        "last_name": "Smith",
        "full_name": "Jordan Smith",
        "slug": "jordan-smith",
        "hometown": "Charlotte, N.C.",
        "high_school": "Myers Park",
        "previous_school": "East Carolina",
        "major": "Economics",
        "gender": "male",
        "short_master_biography": "<p>...</p>"
      }
    }
  ],
  "meta": { "current_page": 1, "last_page": 2, "total": 111 }
}
```

- Use `jersey_number_label`, `jersey_number` is a number so `0` and `00` look the same
- Height and weight are sometimes only on `player`, check both
- Profile pages are at `/sports/{sport slug}/roster/player/{player.slug}`


## Staff on a roster

`GET /website-api/roster-staff-members?filter[roster_id]={rosterId}&include=staffMember,photo,roster.season&per_page=100`

```json
{
  "data": [
    {
      "type": "coach",
      "position": "Head Coach",
      "staff_member": { "first_name": "Chris", "last_name": "Allen", "slug": "chris-allen" },
      "roster": { "season": { "name": "2026", "slug": "2026" } }
    }
  ]
}
```

`type` is `coach` or `support_staff`. `position` is the title.


## Schedule

Two calls. First the schedule itself, mostly for the season name:

`GET /website-api/schedules/{scheduleId}?include=season`

```json
{ "data": { "id": 1588, "name": "Football 2026", "season": { "name": "2026" } } }
```

Then the games:

`GET /website-api/schedule-events?filter[schedule_id]={scheduleId}&include=opponent,opponentLogo,scheduleEventResult&sort=datetime&per_page=100`

```json
{
  "data": [
    {
      "id": 27044,
      "datetime": "2026-09-05T01:00:00.000000Z",
      "is_all_day": false,
      "tba": null,
      "tba_text": null,
      "opponent_name": "Miami",
      "venue_type": "home",
      "location": "Stanford, CA",
      "venue": "Stanford Stadium",
      "is_conference": true,
      "status": "completed",
      "opponent_logo": { "url": "https://gostanford.com/imgproxy/..." },
      "schedule_event_result": {
        "result": "loss",
        "winning_score": "45.0000",
        "losing_score": "6.0000"
      }
    }
  ]
}
```

| Field | Notes |
| --- | --- |
| `datetime` | UTC. Convert with the site timezone, a 6 PM Pacific game is the next day in UTC |
| `tba` | Set (e.g. `time_tba`) when the time isn't announced, `tba_text` has what the site shows |
| `venue_type` | `home`, `away` or `neutral` |
| `schedule_event_result.result` | `win`, `loss` or `tie` |
| `winning_score` / `losing_score` | Decimal strings. Winner first, so flip them for a loss if you want the school's score first |

You can also filter by sport instead of schedule: `filter[schedule.sport_id]={sportId}` with `filter[upcoming]=true` or `filter[past]=true`. That's how the website builds its "upcoming games" strips.


## Other endpoints

Seen in the site's JavaScript, same query style as above.

| Endpoint | What it is |
| --- | --- |
| `/website-api/players`, `/website-api/players/{id}` | Players across all seasons |
| `/website-api/staff-members`, `/website-api/staff-members/{id}` | Staff directory |
| `/website-api/rosters`, `/website-api/rosters/{id}` | Rosters (filter by sport or season) |
| `/website-api/seasons` | Seasons |
| `/website-api/schedules` | Schedules |
| `/website-api/schedule-events/{id}` | One game |


## Gotchas

- Times are UTC, get the timezone from `website-config` first
- Some sports point to a schedule id that's been deleted, `/schedules/{id}` returns 404 for those
- Schools fill in fields differently. BYU puts high schools in `previous_school` for example
- Please be gentle with the request rate
