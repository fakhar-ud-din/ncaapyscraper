# SIDEARM Sports API (unofficial)

SIDEARM Sports runs a big chunk of college athletics websites. The newer SIDEARM sites load everything from a JSON API on the same domain under `/api/v2/`. It's not documented anywhere, there's no key, and it's what the site's own pages call.

This is what I've found by using it. Nothing here is official and any of it can change.

**Is a site on it?** Open `https://<site>/api/v2/Sports`. If you get a JSON array back, it is.

```bash
curl https://goduke.com/api/v2/Sports
```

- [Sports](#sports)
- [Roster by id](#roster-by-id)
- [Roster by sport and season](#roster-by-sport-and-season)
- [Schedule](#schedule)
- [Coaches](#coaches)
- [Other endpoints](#other-endpoints)
- [Gotchas](#gotchas)


## Sports

`GET /api/v2/Sports`

Every sport the site has, with the ids you need for rosters and schedules.

```json
[
  {
    "id": 5,
    "title": "Football",
    "abbrev": "FB",
    "globalSportNameSlug": "football",
    "globalSportShortName": "football",
    "globalSportGender": "m",
    "rosterId": 1207,
    "scheduleId": 996,
    "seasonId": 256
  }
]
```

| Field | Notes |
| --- | --- |
| `id` | Sport id, used by the coaches endpoint |
| `title` | Display name, e.g. `Men's Basketball` |
| `globalSportNameSlug` | Slug used in page urls, e.g. `mens-basketball` |
| `globalSportGender` | `m`, `f` or `g` (co-ed or general) |
| `rosterId` | Current roster, `null` for things like "General" |
| `scheduleId` | Current schedule |
| `seasonId` | Current season |


## Roster by id

`GET /api/v2/Rosters/{rosterId}`

The whole roster in one response: players, coaches and support staff.

```json
{
  "id": 1207,
  "season": { "id": 256, "title": "2026" },
  "sport": { "title": "Football", "globalSportNameSlug": "football" },
  "players": [
    {
      "rosterPlayerId": 24470,
      "firstName": "Jordan",
      "lastName": "Smith",
      "jerseyNumber": "24",
      "positionShort": "RB",
      "positionLong": "Running Back",
      "heightFeet": 5,
      "heightInches": 10,
      "weight": 205,
      "academicYearShort": "Sr.",
      "academicYearLong": "Senior",
      "hometown": "Charlotte, N.C.",
      "highSchool": "Myers Park",
      "previousSchool": "East Carolina",
      "major": "Economics",
      "gender": "M",
      "image": { "url": "/images/2026/7/27/smith.jpg", "absoluteUrl": "https://goduke.com/images/2026/7/27/smith.jpg" },
      "bio": ""
    }
  ],
  "coaches": [
    { "id": 5388, "firstName": "Chris", "lastName": "Allen", "title": "Head Coach", "image": { "absoluteUrl": "..." }, "bio": "<p>...</p>" }
  ],
  "support": [
    { "id": 912, "firstName": "Sam", "lastName": "Lee", "title": "Director of Operations" }
  ]
}
```

- `gender` on a player is `M` or `F`. It matters on co-ed rosters like track and swimming
- `bio` is usually empty here. Full bios come from a per-player endpoint, see [other endpoints](#other-endpoints)
- `coaches` and `support` can come back empty on some sites even when the site shows coaches. Use the next endpoint for those
- Empty rosters come back as `204 No Content`

Player profile pages live at `/sports/{slug}/roster/{first-last}/{rosterPlayerId}` and coaches at `/sports/{slug}/roster/coaches/{first-last}/{id}`.


## Roster by sport and season

`GET /api/v2/Rosters/bySport/{slug}?season={seasonTitle}&includeCoaches=true`

Same roster object as above, looked up by sport slug and season title (`2026`, `2025-26`, whatever the roster's `season.title` says). With `includeCoaches=true` it fills in `coaches` and `support` on the sites where the roster by id leaves them empty.

```bash
curl "https://cuse.com/api/v2/Rosters/bySport/football?season=2026&includeCoaches=true"
```

Use the exact season title. The wrong format (`2025-26` for a sport that uses `2026`) returns a different, mostly empty roster.


## Schedule

`GET /api/v2/Schedule/{scheduleId}`

```json
{
  "id": 996,
  "title": "2026 Football Schedule",
  "season": { "id": 256, "title": "2026" },
  "record": { "overall": "6-2", "conference": "3-2", "streak": "W2", "home": "4-1", "away": "2-1", "neutral": "0-0" },
  "games": [
    {
      "id": 25756,
      "date": "2026-09-05T17:00:00",
      "dateUtc": "2026-09-05T21:00:00Z",
      "time": "5 p.m.",
      "opponent": { "title": "Tulane", "image": { "fullpath": "/images/logos/Tulane-Wave.png" } },
      "locationIndicator": "H",
      "atVs": "vs",
      "location": "Durham, N.C.",
      "facility": { "title": "Brooks Field at Wallace Wade Stadium" },
      "conference": false,
      "tournament": null,
      "media": { "tv": "ACC Network", "radio": "" },
      "result": { "status": "W", "teamScore": "17", "opponentScore": "3" }
    }
  ]
}
```

| Field | Notes |
| --- | --- |
| `date` | Local date and time of the school |
| `dateUtc` | Same moment in UTC |
| `time` | Text as shown on the site, `5 p.m.`, `TBA`, `All Day` |
| `locationIndicator` | `H` home, `A` away, `N` neutral |
| `conference` | `true` for conference games |
| `result.status` | `W`, `L`, `T`, or `N` for no result yet / exhibition |
| `result.teamScore` | Always the school's own score |

Some events (track meets, golf tournaments) have no `opponent` and use `eventName` instead. On some sites `record.overall` comes wrapped in HTML (`<span class='record_wins'>6</span> - ...`), strip the tags.


## Coaches

`GET /api/v2/Staff/coaches?sportId={sportId}`

Paginated list of coaches for a sport. Handy if all you want is the coaching staff.

```json
{ "items": [ { "firstName": "Fran", "lastName": "Brown", "title": "Head Coach" } ], "total": 10, "page": 1, "pages": 1 }
```

`GET /api/v2/Staff?sportId={sportId}` returns the whole staff directory instead (athletic director, admin and so on).


## Other endpoints

These show up in the site's own JavaScript. I haven't used them in this project, so treat the parameters as a starting point.

| Endpoint | What it looks like |
| --- | --- |
| `/api/v2/Players/roster/bio/{rosterPlayerId}/responsive?sportSlug={slug}&year={year}` | Full player bio, one request per player |
| `/api/v2/Rosters/list?sport={...}` | Looks like past seasons for a sport, returned `[]` with the sport id so the parameter is probably something else |
| `/api/v2/Schedule/{scheduleId}/Record` | The schedule's record plus sport info |
| `/api/v2/ScheduleGames/{gameId}` | One game |
| `/api/v2/Stats/{sportSlug}/season/{season}` | Season stats |
| `/api/v2/navigation` | Site navigation |


## Gotchas

- Some sites only answer on `www.` (`www.kstatesports.com`). Follow redirects
- `date` is local, `dateUtc` is UTC. The text `time` is what a fan sees
- Rosters and schedules are for the current season unless you ask for another one
- Please be gentle. These are school websites, a few requests a second is plenty
