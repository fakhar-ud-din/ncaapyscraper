from ncaapyscraper import list_schools
from ncaapyscraper.platforms import PLATFORMS
from ncaapyscraper.schools import SCHOOLS, conference_name, find_school, pick_schools


def test_registry_loads():
    assert len(SCHOOLS) > 900
    assert all(school['platform'] in PLATFORMS for school in SCHOOLS.values())
    assert all(school['site'] and school['name'] for school in SCHOOLS.values())


def test_find_school():
    assert find_school('duke')['site'] == 'goduke.com'
    assert find_school('https://www.goduke.com/')['key'] == 'duke'
    assert find_school('navy')['key'] == 'us_naval_academy'
    assert find_school('not_a_school') is None


def test_custom_school():
    school = find_school({'name': 'Boise State', 'site': 'broncosports.com', 'platform': 'sidearm'})
    assert school['key'] == 'broncosports'
    assert school['division'] == 0


def test_conferences_and_divisions():
    assert conference_name('sec') == 'Southeastern Conference'
    assert conference_name('big sky') == 'Big Sky Conference'
    assert len(pick_schools('sec')) == 16
    assert all(SCHOOLS[key]['subdivision'] == 'FBS' for key in pick_schools(division='fbs'))
    assert list_schools('acc')[0].keys() >= {'key', 'name', 'site', 'platform'}
