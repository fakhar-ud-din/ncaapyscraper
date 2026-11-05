from ncaapyscraper.utils import (
    clean_opponent,
    format_score,
    format_time,
    is_time,
    normalize_height,
    parse_month_day,
    season_dates,
    sport_key,
    split_arg,
    split_result,
    sports_gender,
    to_local,
    utc_text,
)


def test_format_time():
    assert format_time('7 p.m.') == '7:00 PM'
    assert format_time('12:45 pm') == '12:45 PM'
    assert format_time('Noon') == '12:00 PM'
    assert format_time('3:15 PM ET') == '3:15 PM'
    assert format_time('TBA') == 'TBA'


def test_split_result_puts_school_score_first():
    assert split_result('W, 31-14') == ('W', '31-14')
    assert split_result('L, 43-10') == ('L', '10-43')
    assert split_result('W', '57-0') == ('W', '57-0')
    assert split_result('W, 3-2 (OT)') == ('W', '3-2 (OT)')
    assert split_result('Blue 23, White 18') == ('', 'Blue 23, White 18')


def test_clean_opponent():
    assert clean_opponent('at #20 Utah') == 'Utah'
    assert clean_opponent('vs. Youngstown State') == 'Youngstown State'
    assert clean_opponent('Atlanta Tipoff') == 'Atlanta Tipoff'


def test_dates():
    assert parse_month_day('Sat. Apr 18') == (4, 18)
    assert parse_month_day('Sept. 5') == (9, 5)
    assert season_dates([(10, 2), (12, 20), (1, 3)], 2026) == ['2026-10-02', '2026-12-20', '2027-01-03']


def test_times_and_zones():
    assert utc_text('2026-08-29T23:00:00.000000Z') == '2026-08-29T23:00:00Z'
    local = to_local('2026-09-05T01:00:00.000000Z', 'America/Los_Angeles')
    assert local.strftime('%Y-%m-%d %H:%M') == '2026-09-04 18:00'
    assert is_time('7:00 PM') and is_time('TBA') and not is_time('W, 31-14')


def test_sports():
    assert sports_gender("Men's Basketball") == 'men'
    assert sports_gender('Women’s Golf') == 'women'
    assert sports_gender('Football') == 'men'
    assert sports_gender('Track & Field') == ''
    assert sport_key("Men's Swimming & Diving") == 'mens-swimming-and-diving'
    assert split_arg(['football,baseball', 'golf']) == ['football', 'baseball', 'golf']


def test_numbers():
    assert normalize_height('6\'0"') == '6-0'
    assert normalize_height("6' 2''") == '6-2'
    assert format_score('37.0000') == '37'
    assert format_score('197.3750') == '197.375'
