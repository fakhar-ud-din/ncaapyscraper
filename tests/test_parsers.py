from ncaapyscraper.client import Page
from ncaapyscraper.items import TeamScheduleItem
from ncaapyscraper.output import school_result
from ncaapyscraper.platforms.sidearm import SidearmParser
from ncaapyscraper.platforms.sidearm_legacy import SidearmLegacyParser
from ncaapyscraper.platforms.wmt import WmtParser
from ncaapyscraper.schools import find_school


META = {'sports_name': 'Football', 'slug': 'football', 'gender': 'men'}


def test_sidearm_roster_and_schedule():
    parser = SidearmParser(find_school('duke'))
    page = Page('https://goduke.com/api/v2/Rosters/1', 200, '', META)

    roster = {
        'season': {'title': '2026'},
        'players': [{'rosterPlayerId': 7, 'firstName': 'Jordan', 'lastName': 'Smith', 'jerseyNumber': '24', 'positionShort': 'RB', 'heightFeet': 5, 'heightInches': 10, 'weight': 205, 'academicYearLong': 'Senior', 'hometown': 'Charlotte, N.C.'}],
        'coaches': [{'id': 9, 'firstName': 'Chris', 'lastName': 'Allen', 'title': 'Head Coach'}],
    }
    player = list(parser.parse_players(page, roster))[0]
    assert (player['name'], player['height'], player['weight'], player['season']) == ('Jordan Smith', '5-10', '205', '2026')
    assert player['profile_url'] == 'https://goduke.com/sports/football/roster/jordan-smith/7'
    assert list(parser.parse_coaches(page, roster))[0]['title'] == 'Head Coach'

    schedule = {'games': [{'date': '2026-09-05T17:00:00', 'dateUtc': '2026-09-05T21:00:00Z', 'time': '5 p.m.', 'opponent': {'title': 'Tulane'}, 'locationIndicator': 'H', 'conference': False, 'result': {'status': 'W', 'teamScore': '17', 'opponentScore': '3'}}]}
    game = list(parser.parse_schedule(page, schedule))[0]
    assert (game['date'], game['time'], game['home_away'], game['result'], game['score']) == ('2026-09-05', '5:00 PM', 'home', 'W', '17-3')


def test_wmt_schedule_uses_school_timezone():
    parser = WmtParser(find_school('stanford'))
    page = Page('https://gostanford.com/website-api/schedule-events', 200, '', {**META, 'timezone': 'America/Los_Angeles'})

    data = {'data': [{'datetime': '2026-09-05T01:00:00.000000Z', 'opponent_name': 'Miami', 'venue_type': 'home', 'is_conference': True, 'schedule_event_result': {'result': 'loss', 'winning_score': '45.0000', 'losing_score': '6.0000'}}]}
    game = list(parser.parse_schedule(page, data))[0]
    assert (game['date'], game['time'], game['score'], game['result']) == ('2026-09-04', '6:00 PM', '6-45', 'L')


ROSTER_HTML = '''<html><head><title>2026 Football Roster - Villanova</title></head><body>
<ul><li class="sidearm-roster-player" data-player-url="/sports/football/roster/josiah-adams/16235">
  <div class="sidearm-roster-player-image"><img data-src="https://cdn.example.com/adams.jpg?width=80"></div>
  <div class="sidearm-roster-player-position"><span class="text-bold"> DB </span><span class="sidearm-roster-player-height">6'0"</span><span class="sidearm-roster-player-weight">165 lbs</span></div>
  <div class="sidearm-roster-player-name"><span class="sidearm-roster-player-jersey-number"> 37 </span><h3><a>Josiah Adams</a></h3></div>
  <span class="sidearm-roster-player-academic-year">Fr.</span><span class="sidearm-roster-player-academic-year">Freshman</span>
  <span class="sidearm-roster-player-hometown">Upper Darby, Pa.</span><span class="sidearm-roster-player-highschool">Bonner-Prendie</span>
</li></ul>
<ul><li class="sidearm-roster-coach"><div class="sidearm-roster-coach-title"><span>Head Coach</span></div><div class="sidearm-roster-coach-name"><p>Mark Ferrante</p></div></li></ul>
</body></html>'''

SCHEDULE_HTML = '''<html><head><title>2026 Football Schedule</title>
<script type="application/ld+json">[{"@type": "SportsEvent", "startDate": "2026-08-28T18:00:00"}]</script></head><body><ul>
<li class="sidearm-schedule-game sidearm-schedule-home-game">
  <div class="sidearm-schedule-game-opponent-date"><span>Aug 28 (Fri)</span><span>6:00 PM</span></div>
  <div class="sidearm-schedule-game-opponent-name"><a>William &amp; Mary</a></div>
  <div class="sidearm-schedule-game-location"><span>Villanova, Pa.</span><span><a>Villanova Stadium</a></span></div>
  <span class="sidearm-schedule-game-conference">Patriot League</span>
  <div class="sidearm-schedule-game-result"><span>L,</span><span>32-35</span></div>
</li></ul></body></html>'''


def test_sidearm_legacy_pages():
    parser = SidearmLegacyParser(find_school('villanova'))

    items = list(parser.parse_roster(Page('https://villanova.com/sports/football/roster', 200, ROSTER_HTML, META)))
    player, coach = items
    assert (player['name'], player['shirt_no'], player['height'], player['weight'], player['player_class']) == ('Josiah Adams', '37', '6-0', '165', 'Freshman')
    assert player['image_url'] == 'https://cdn.example.com/adams.jpg'
    assert (coach['name'], coach['title'], coach['is_coach']) == ('Mark Ferrante', 'Head Coach', 1)

    game = list(parser.parse_schedule(Page('https://villanova.com/sports/football/schedule', 200, SCHEDULE_HTML, META)))[0]
    assert isinstance(game, TeamScheduleItem)
    assert (game['date'], game['time'], game['opponent'], game['home_away'], game['venue']) == ('2026-08-28', '6:00 PM', 'William & Mary', 'home', 'Villanova Stadium')
    assert (game['result'], game['score'], game['is_conference']) == ('L', '32-35', 1)

    result = school_result(find_school('villanova'), items + [game], ['players', 'schedules'])
    sport = result['sports'][0]
    assert set(sport) == {'sport', 'gender', 'season', 'players', 'schedule'}
    assert sport['players'][0]['weight'] == 165
